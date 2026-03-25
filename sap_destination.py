"""
SAP BTP Destination Service Client

Handles:
1. Fetching XSUAA OAuth2 token for the Destination service
2. Retrieving destination details from SAP BTP Destination service
3. Making authenticated HTTP calls to S/4HANA via the destination
"""

import os
import logging
import time
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TokenCache:
    """Simple in-memory token cache with expiry."""

    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[str]:
        if self._token and time.time() < self._expires_at - 30:
            return self._token
        return None

    def set(self, token: str, expires_in: int):
        self._token = token
        self._expires_at = time.time() + expires_in


class SAPDestinationClient:
    """
    Client for SAP BTP Destination Service.

    Reads connection details from environment variables:

    BTP Destination Service mode (recommended):
      DESTINATION_SERVICE_AUTH_URL      XSUAA token URL for Destination service
                                        e.g. https://<subdomain>.authentication.<region>.hana.ondemand.com/oauth/token
      DESTINATION_SERVICE_CLIENT_ID     OAuth2 client ID (from Destination service binding)
      DESTINATION_SERVICE_CLIENT_SECRET OAuth2 client secret
      DESTINATION_SERVICE_URL           Destination service REST API base URL
                                        e.g. https://destination-configuration.cfapps.<region>.hana.ondemand.com
      DESTINATION_NAME                  Name of the destination configured in BTP cockpit

    Direct connection mode (for local development / testing):
      S4_BASE_URL                       Direct S/4HANA base URL (e.g. https://my-s4.example.com)
      S4_USERNAME                       Basic auth username
      S4_PASSWORD                       Basic auth password
    """

    S4_ODATA_BASE = "/sap/opu/odata/sap/API_PRODUCT_SRV"

    def __init__(self):
        # Destination service credentials
        self.dest_auth_url = os.getenv("DESTINATION_SERVICE_AUTH_URL", "")
        self.dest_client_id = os.getenv("DESTINATION_SERVICE_CLIENT_ID", "")
        self.dest_client_secret = os.getenv("DESTINATION_SERVICE_CLIENT_SECRET", "")
        self.dest_service_url = os.getenv("DESTINATION_SERVICE_URL", "")
        self.destination_name = os.getenv("DESTINATION_NAME", "")

        # Direct connection fallback
        self.s4_base_url = os.getenv("S4_BASE_URL", "")
        self.s4_username = os.getenv("S4_USERNAME", "")
        self.s4_password = os.getenv("S4_PASSWORD", "")

        # Token caches
        self._dest_token_cache = TokenCache()
        self._s4_token_cache = TokenCache()

        # Cached destination details
        self._destination_details: Optional[Dict[str, Any]] = None
        self._destination_cached_at: float = 0.0
        self._destination_cache_ttl: int = 300  # 5 minutes

        # Determine mode
        self.use_destination_service = bool(
            self.dest_auth_url
            and self.dest_client_id
            and self.dest_client_secret
            and self.dest_service_url
            and self.destination_name
        )

        if self.use_destination_service:
            logger.info("SAP client configured with BTP Destination Service (destination: %s)", self.destination_name)
        elif self.s4_base_url:
            logger.info("SAP client configured with direct S/4HANA connection (%s)", self.s4_base_url)
        else:
            logger.warning(
                "SAP client: no connection configured. "
                "Set DESTINATION_* env vars for BTP Destination Service, "
                "or S4_BASE_URL / S4_USERNAME / S4_PASSWORD for direct connection."
            )

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _get_destination_service_token(self) -> str:
        """Fetch (or return cached) OAuth2 token for the BTP Destination service."""
        cached = self._dest_token_cache.get()
        if cached:
            return cached

        logger.debug("Fetching new Destination service token from %s", self.dest_auth_url)
        resp = requests.post(
            self.dest_auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.dest_client_id,
                "client_secret": self.dest_client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._dest_token_cache.set(token, expires_in)
        return token

    # ------------------------------------------------------------------
    # Destination resolution
    # ------------------------------------------------------------------

    def _get_destination_details(self) -> Dict[str, Any]:
        """Retrieve destination configuration from BTP Destination service."""
        now = time.time()
        if self._destination_details and (now - self._destination_cached_at) < self._destination_cache_ttl:
            return self._destination_details

        token = self._get_destination_service_token()
        url = f"{self.dest_service_url.rstrip('/')}/destination-configuration/v1/destinations/{self.destination_name}"
        logger.debug("Fetching destination details from %s", url)

        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
        details = resp.json()
        self._destination_details = details
        self._destination_cached_at = now
        return details

    def _build_s4_session(self) -> tuple[str, requests.Session]:
        """
        Build a requests.Session pre-configured for S/4HANA calls.

        Returns (base_url, session).
        """
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})

        if self.use_destination_service:
            details = self._get_destination_details()
            dest_config = details.get("destinationConfiguration", {})

            base_url = dest_config.get("URL", "").rstrip("/")
            auth_type = dest_config.get("Authentication", "NoAuthentication")

            if auth_type == "BasicAuthentication":
                session.auth = (dest_config.get("User", ""), dest_config.get("Password", ""))

            elif auth_type in ("OAuth2ClientCredentials", "OAuth2SAMLBearerAssertion"):
                # Use the authTokens provided by the Destination service
                auth_tokens = details.get("authTokens", [])
                if auth_tokens:
                    token_entry = auth_tokens[0]
                    token_type = token_entry.get("type", "Bearer")
                    token_value = token_entry.get("value", "")
                    session.headers["Authorization"] = f"{token_type} {token_value}"
                else:
                    logger.warning("No authTokens found in destination response for OAuth2 destination")

            elif auth_type == "NoAuthentication":
                pass  # No auth needed

            else:
                logger.warning("Unsupported destination auth type: %s", auth_type)

            # Additional headers from destination
            for key, value in dest_config.items():
                if key.startswith("URL.headers."):
                    header_name = key[len("URL.headers."):]
                    session.headers[header_name] = value

        else:
            # Direct connection
            base_url = self.s4_base_url.rstrip("/")
            if self.s4_username and self.s4_password:
                session.auth = (self.s4_username, self.s4_password)

        return base_url, session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, odata_path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the S/4HANA API_PRODUCT_SRV OData service.

        Args:
            odata_path: Path relative to the OData service root,
                        e.g. "/A_Product" or "/A_Product('TG11')"
            params:     Optional dict of OData query parameters
                        ($top, $skip, $filter, $select, $orderby, $expand, $format)

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            requests.HTTPError: on non-2xx responses
            RuntimeError: if no connection is configured
        """
        if not self.use_destination_service and not self.s4_base_url:
            raise RuntimeError(
                "No SAP connection configured. "
                "Set DESTINATION_* env vars or S4_BASE_URL / S4_USERNAME / S4_PASSWORD."
            )

        base_url, session = self._build_s4_session()
        url = f"{base_url}{self.S4_ODATA_BASE}{odata_path}"

        # Always request JSON
        query_params = {"$format": "json"}
        if params:
            query_params.update({k: v for k, v in params.items() if v is not None})

        logger.info("GET %s params=%s", url, query_params)

        resp = session.get(url, params=query_params, timeout=30)
        resp.raise_for_status()
        return resp.json()