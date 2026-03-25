"""
SAP BTP Destination Service Client

Handles:
1. Fetching XSUAA OAuth2 token for the Destination service
2. Retrieving destination details from SAP BTP Destination service
3. Making authenticated HTTP calls to S/4HANA via the destination

Supported destination authentication types
------------------------------------------
- BasicAuthentication          – username/password injected by Destination service
- OAuth2ClientCredentials      – Bearer token from authTokens in destination response
- OAuth2SAMLBearerAssertion    – Bearer token from authTokens in destination response
- PrincipalPropagation         – routes through CF Connectivity on-premise proxy
                                 (requires Connectivity service bound to the app)
- NoAuthentication             – no auth header

Credential resolution order
---------------------------
1. VCAP_SERVICES (automatic when services are bound to the CF app)
   Only DESTINATION_NAME still needs to be set as an env var.

2. DESTINATION_SERVICE_* environment variables (local dev / manual override)

3. S4_BASE_URL / S4_USERNAME / S4_PASSWORD (direct connection, local dev only)
"""

import json
import os
import logging
import time
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# VCAP_SERVICES helpers
# ---------------------------------------------------------------------------

def _read_vcap_service(label: str) -> Optional[Dict[str, Any]]:
    """
    Parse VCAP_SERVICES and return the credentials block of the first
    bound service instance with the given label, or None if not present.
    """
    vcap_raw = os.getenv("VCAP_SERVICES", "")
    if not vcap_raw:
        return None
    try:
        vcap = json.loads(vcap_raw)
    except json.JSONDecodeError:
        logger.warning("VCAP_SERVICES is set but could not be parsed as JSON")
        return None

    instances = vcap.get(label, [])
    if instances:
        creds = instances[0].get("credentials", {})
        if creds:
            logger.debug("Found '%s' credentials in VCAP_SERVICES", label)
            return creds

    return None


def _read_vcap_destination() -> Optional[Dict[str, Any]]:
    """
    Return credentials for the bound Destination service instance.

    Relevant keys:
      clientid     – OAuth2 client ID
      clientsecret – OAuth2 client secret
      uri          – Destination service REST API base URL
      url          – XSUAA base URL  (token URL = url + "/oauth/token")
    """
    creds = _read_vcap_service("destination")
    if creds and creds.get("clientid") and creds.get("uri"):
        return creds
    return None


def _read_vcap_connectivity() -> Optional[Dict[str, Any]]:
    """
    Return credentials for the bound Connectivity service instance.

    Relevant keys:
      clientid               – OAuth2 client ID for proxy token
      clientsecret           – OAuth2 client secret
      token_service_url      – XSUAA token URL
      onpremise_proxy_host   – CF Connectivity proxy hostname
      onpremise_proxy_port   – CF Connectivity proxy port (HTTPS tunnel)
      onpremise_proxy_http_port – CF Connectivity proxy port (HTTP tunnel)
    """
    creds = _read_vcap_service("connectivity")
    if creds and creds.get("onpremise_proxy_host"):
        return creds
    return None


# ---------------------------------------------------------------------------
# Token cache
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class SAPDestinationClient:
    """
    Client for SAP BTP Destination Service.

    Credential resolution order:

    1. VCAP_SERVICES  (automatic when services are bound to the CF app)
       Only DESTINATION_NAME still needs to be set as an env var.

    2. Manual env vars  (local development / CI):
         DESTINATION_SERVICE_AUTH_URL      XSUAA token URL
         DESTINATION_SERVICE_CLIENT_ID     OAuth2 client ID
         DESTINATION_SERVICE_CLIENT_SECRET OAuth2 client secret
         DESTINATION_SERVICE_URL           Destination service REST API base URL
         DESTINATION_NAME                  Destination name in BTP cockpit

    3. Direct S/4HANA connection  (local dev / testing without BTP):
         S4_BASE_URL    Direct S/4HANA base URL
         S4_USERNAME    Basic auth username
         S4_PASSWORD    Basic auth password
    """

    S4_ODATA_BASE = "/sap/opu/odata/sap/API_PRODUCT_SRV"

    def __init__(self):
        self.destination_name = os.getenv("DESTINATION_NAME", "")

        # ------------------------------------------------------------------
        # Priority 1: VCAP_SERVICES (CF bound services)
        # ------------------------------------------------------------------
        vcap_dest = _read_vcap_destination()
        vcap_conn = _read_vcap_connectivity()

        if vcap_dest and self.destination_name:
            xsuaa_base = vcap_dest.get("url", "").rstrip("/")
            if not xsuaa_base.endswith("/oauth/token"):
                xsuaa_base = xsuaa_base + "/oauth/token"

            self.dest_auth_url = xsuaa_base
            self.dest_client_id = vcap_dest.get("clientid", "")
            self.dest_client_secret = vcap_dest.get("clientsecret", "")
            self.dest_service_url = vcap_dest.get("uri", "").rstrip("/")
            logger.info(
                "Destination service credentials loaded from VCAP_SERVICES "
                "(destination: %s)", self.destination_name
            )

        # ------------------------------------------------------------------
        # Priority 2: manual DESTINATION_SERVICE_* env vars
        # ------------------------------------------------------------------
        else:
            vcap_conn = None  # Connectivity proxy only available via VCAP
            self.dest_auth_url = os.getenv("DESTINATION_SERVICE_AUTH_URL", "")
            self.dest_client_id = os.getenv("DESTINATION_SERVICE_CLIENT_ID", "")
            self.dest_client_secret = os.getenv("DESTINATION_SERVICE_CLIENT_SECRET", "")
            self.dest_service_url = os.getenv("DESTINATION_SERVICE_URL", "")
            if self.dest_auth_url:
                logger.info(
                    "Destination service credentials loaded from env vars "
                    "(destination: %s)", self.destination_name
                )

        # ------------------------------------------------------------------
        # Connectivity service (PrincipalPropagation / on-premise proxy)
        # ------------------------------------------------------------------
        if vcap_conn:
            # token_service_url is the full token endpoint URL in most bindings.
            # Some bindings provide only "url" (XSUAA base) — append /oauth/token.
            # Either way, ensure the path ends with /oauth/token.
            raw_token_url = (
                vcap_conn.get("token_service_url", "")
                or vcap_conn.get("url", "")
            ).rstrip("/")
            if raw_token_url and not raw_token_url.endswith("/oauth/token"):
                raw_token_url = raw_token_url + "/oauth/token"
            self._conn_token_url = raw_token_url

            self._conn_client_id = vcap_conn.get("clientid", "")
            self._conn_client_secret = vcap_conn.get("clientsecret", "")
            self._conn_proxy_host = vcap_conn.get("onpremise_proxy_host", "")
            # Prefer the HTTP tunnel port; fall back to the generic proxy port
            self._conn_proxy_port = (
                vcap_conn.get("onpremise_proxy_http_port")
                or vcap_conn.get("onpremise_proxy_port", "20003")
            )
            logger.info(
                "Connectivity service loaded from VCAP_SERVICES "
                "(proxy: %s:%s, token_url: %s)",
                self._conn_proxy_host, self._conn_proxy_port, self._conn_token_url
            )
        else:
            self._conn_token_url = ""
            self._conn_client_id = ""
            self._conn_client_secret = ""
            self._conn_proxy_host = ""
            self._conn_proxy_port = ""

        # ------------------------------------------------------------------
        # Priority 3: direct S/4HANA connection
        # ------------------------------------------------------------------
        self.s4_base_url = os.getenv("S4_BASE_URL", "")
        self.s4_username = os.getenv("S4_USERNAME", "")
        self.s4_password = os.getenv("S4_PASSWORD", "")

        # Token caches
        self._dest_token_cache = TokenCache()
        self._conn_token_cache = TokenCache()

        # Cached destination details
        self._destination_details: Optional[Dict[str, Any]] = None
        self._destination_cached_at: float = 0.0
        self._destination_cache_ttl: int = 300  # 5 minutes

        # Determine active mode
        self.use_destination_service = bool(
            self.dest_auth_url
            and self.dest_client_id
            and self.dest_client_secret
            and self.dest_service_url
            and self.destination_name
        )

        if self.use_destination_service:
            logger.info(
                "SAP client mode: BTP Destination Service (destination: %s)",
                self.destination_name,
            )
        elif self.s4_base_url:
            logger.info(
                "SAP client mode: direct S/4HANA connection (%s)", self.s4_base_url
            )
        else:
            logger.warning(
                "SAP client: no connection configured. "
                "Bind the Destination service to this app and set DESTINATION_NAME, "
                "or set DESTINATION_SERVICE_* env vars, "
                "or set S4_BASE_URL / S4_USERNAME / S4_PASSWORD for a direct connection."
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
        try:
            data = resp.json()
        except ValueError as exc:
            raw = resp.text[:300] if resp.text else "(empty body)"
            raise RuntimeError(
                f"Destination service token endpoint returned non-JSON "
                f"(HTTP {resp.status_code}): {raw}"
            ) from exc
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._dest_token_cache.set(token, expires_in)
        return token

    def _get_connectivity_proxy_token(self) -> str:
        """
        Fetch (or return cached) OAuth2 token for the CF Connectivity proxy.

        This token is sent as Proxy-Authorization when routing requests
        through the on-premise proxy for PrincipalPropagation destinations.
        """
        cached = self._conn_token_cache.get()
        if cached:
            return cached

        if not self._conn_token_url:
            raise RuntimeError(
                "Connectivity service is not bound to this app. "
                "Bind the 'connectivity' service instance to use "
                "PrincipalPropagation destinations."
            )

        logger.debug("Fetching new Connectivity proxy token from %s", self._conn_token_url)
        resp = requests.post(
            self._conn_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._conn_client_id,
                "client_secret": self._conn_client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as exc:
            raw = resp.text[:300] if resp.text else "(empty body)"
            raise RuntimeError(
                f"Connectivity service token endpoint returned non-JSON "
                f"(HTTP {resp.status_code}): {raw}"
            ) from exc
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._conn_token_cache.set(token, expires_in)
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
        url = (
            f"{self.dest_service_url}/destination-configuration/v1"
            f"/destinations/{self.destination_name}"
        )
        logger.debug("Fetching destination details from %s", url)

        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
        try:
            details = resp.json()
        except ValueError as exc:
            raw = resp.text[:300] if resp.text else "(empty body)"
            raise RuntimeError(
                f"Destination service returned non-JSON for destination '{self.destination_name}' "
                f"(HTTP {resp.status_code}): {raw}"
            ) from exc
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
                    logger.warning(
                        "No authTokens found in destination response for OAuth2 destination"
                    )

            elif auth_type == "PrincipalPropagation":
                # Route through the CF Connectivity on-premise proxy.
                # The proxy handles authentication to the on-premise system.
                proxy_token = self._get_connectivity_proxy_token()
                proxy_url = f"http://{self._conn_proxy_host}:{self._conn_proxy_port}"
                session.proxies = {"http": proxy_url, "https": proxy_url}
                session.headers["Proxy-Authorization"] = f"Bearer {proxy_token}"

                # If the destination specifies a Cloud Connector location ID, pass it
                location_id = dest_config.get("CloudConnectorLocationId", "")
                if location_id:
                    session.headers["SAP-Connectivity-SCC-Location_ID"] = location_id

                logger.debug(
                    "PrincipalPropagation: routing via %s (location: %s)",
                    proxy_url, location_id or "default",
                )

            elif auth_type == "NoAuthentication":
                pass  # No auth needed

            else:
                logger.warning("Unsupported destination auth type: %s", auth_type)

            # If the destination targets an on-premise system (ProxyType=OnPremise),
            # route through the CF Connectivity proxy regardless of auth type.
            # This applies to BasicAuthentication, OAuth2, and NoAuthentication
            # destinations that point to an internal host via Cloud Connector.
            # (PrincipalPropagation already sets the proxy above.)
            proxy_type = dest_config.get("ProxyType", "Internet")
            if proxy_type == "OnPremise" and auth_type != "PrincipalPropagation":
                proxy_token = self._get_connectivity_proxy_token()
                proxy_url = f"http://{self._conn_proxy_host}:{self._conn_proxy_port}"
                session.proxies = {"http": proxy_url, "https": proxy_url}
                session.headers["Proxy-Authorization"] = f"Bearer {proxy_token}"
                location_id = dest_config.get("CloudConnectorLocationId", "")
                if location_id:
                    session.headers["SAP-Connectivity-SCC-Location_ID"] = location_id
                logger.debug(
                    "OnPremise destination: routing via %s (location: %s)",
                    proxy_url, location_id or "default",
                )

            # Additional headers from destination (URL.headers.*)
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
                "Bind the Destination service to this app and set DESTINATION_NAME, "
                "or set DESTINATION_SERVICE_* env vars, "
                "or set S4_BASE_URL / S4_USERNAME / S4_PASSWORD."
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
        try:
            return resp.json()
        except ValueError as exc:
            # Response was not valid JSON — log the raw body to help diagnose
            raw = resp.text[:500] if resp.text else "(empty body)"
            raise RuntimeError(
                f"S/4HANA returned a non-JSON response (HTTP {resp.status_code}). "
                f"Raw body: {raw}"
            ) from exc
