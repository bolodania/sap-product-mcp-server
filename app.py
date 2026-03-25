"""
SAP Product Master MCP Server
==============================
Flask application implementing the MCP (Model Context Protocol) over two transports:

  1. Streamable HTTP (MCP spec 2025-03-26) — used by SAP Joule Studio
       POST /mcp    Client sends JSON-RPC request; server returns JSON-RPC response directly.
       GET  /mcp    Returns server metadata (for discovery/health checks).

  2. HTTP + SSE (legacy transport) — used by Claude Desktop and other SSE-based clients
       GET  /sse            SSE stream: server pushes JSON-RPC responses to client
       POST /messages       Client sends JSON-RPC requests; server replies via SSE

  3. Liveness probe
       GET  /health

Architecture:
    Joule / MCP Client
        |  (MCP tool call — Streamable HTTP POST /mcp  OR  SSE GET /sse)
    This Flask MCP Server
        |
    SAP BTP Destination Service  (OAuth2 token + destination lookup)
        |
    S/4HANA API_PRODUCT_SRV  (OData v2 GET calls)

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python app.py
"""

from __future__ import annotations

import json
import logging
import os
import queue
import sys
import threading
import uuid
from typing import Any, Dict, Optional

from flask import Flask, Response, jsonify, request, stream_with_context
from dotenv import load_dotenv

from sap_destination import SAPDestinationClient
from tools import TOOLS, TOOLS_BY_NAME
from tool_executor import execute_tool

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class _SuppressGetMcp(logging.Filter):
    """
    Suppress noisy werkzeug access log lines for GET /mcp.

    Joule Studio polls GET /mcp every few seconds for health/discovery.
    These lines clutter the log and make it hard to spot actual tool calls.
    POST /mcp, GET /health, GET /sse, and all other requests remain visible.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return '"GET /mcp ' not in record.getMessage()


logging.getLogger("werkzeug").addFilter(_SuppressGetMcp())

# ---------------------------------------------------------------------------
# Flask app + SAP client
# ---------------------------------------------------------------------------
app = Flask(__name__)
sap = SAPDestinationClient()

# ---------------------------------------------------------------------------
# MCP server metadata
# ---------------------------------------------------------------------------
MCP_SERVER_NAME = "sap-product-mcp-server"
MCP_SERVER_VERSION = "1.0.0"
MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_PROTOCOL_VERSION_STREAMABLE = "2025-03-26"

# ---------------------------------------------------------------------------
# Session management (one queue per SSE connection)
# ---------------------------------------------------------------------------
_sessions: Dict[str, queue.Queue] = {}
_sessions_lock = threading.Lock()


def _new_session():
    sid = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    with _sessions_lock:
        _sessions[sid] = q
    return sid, q


def _push(sid: str, message: dict) -> bool:
    with _sessions_lock:
        q = _sessions.get(sid)
    if q is None:
        return False
    q.put(message)
    return True


def _remove_session(sid: str):
    with _sessions_lock:
        _sessions.pop(sid, None)


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str, data: Any = None) -> dict:
    error: dict = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


# ---------------------------------------------------------------------------
# MCP message handler (shared by both transports)
# ---------------------------------------------------------------------------

def _handle_message(sid: str, msg: dict) -> Optional[dict]:
    """
    Process a single JSON-RPC 2.0 message and return the response dict
    (or None for notifications that require no response).
    """
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    logger.info("MCP [%s] method=%s id=%s", sid[:8], method, req_id)

    # ---- initialize -------------------------------------------------------
    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            },
            "capabilities": {
                "tools": {},
            },
        })

    # ---- initialized (notification, no response) --------------------------
    if method == "notifications/initialized":
        return None

    # ---- ping -------------------------------------------------------------
    if method == "ping":
        return _ok(req_id, {})

    # ---- tools/list -------------------------------------------------------
    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    # ---- tools/call -------------------------------------------------------
    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        if tool_name not in TOOLS_BY_NAME:
            return _err(req_id, -32602, f"Unknown tool: {tool_name}")

        try:
            result = execute_tool(sap, tool_name, tool_args)
            return _ok(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ],
                "isError": False,
            })
        except ValueError as exc:
            return _err(req_id, -32602, str(exc))
        except RuntimeError as exc:
            return _err(req_id, -32603, str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error executing tool %s", tool_name)
            return _err(req_id, -32603, "Internal error", str(exc))

    # ---- unknown method ---------------------------------------------------
    if req_id is not None:
        return _err(req_id, -32601, f"Method not found: {method}")

    # Notification with unknown method -- silently ignore
    return None


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/mcp", methods=["GET", "POST"])
def mcp_streamable():
    """
    Streamable HTTP transport endpoint (MCP spec 2025-03-26).

    Used by SAP Joule Studio and other modern MCP clients that POST JSON-RPC
    requests and expect a synchronous JSON-RPC response in the HTTP body.

    GET  /mcp  -- server metadata (discovery / health check)
    POST /mcp  -- process JSON-RPC request, return JSON-RPC response directly
    """
    if request.method == "GET":
        return jsonify({
            "server": MCP_SERVER_NAME,
            "version": MCP_SERVER_VERSION,
            "protocol": MCP_PROTOCOL_VERSION_STREAMABLE,
            "transport": "streamable-http",
        })

    # POST -- process JSON-RPC message(s)
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Handle both single message and batch
    is_batch = isinstance(body, list)
    messages_list = body if is_batch else [body]

    responses = []
    for msg in messages_list:
        try:
            resp = _handle_message("streamable", msg)
            if resp is not None:
                responses.append(resp)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Unhandled error in /mcp for message: %s", msg)

    if not responses:
        # All notifications -- no response body needed
        return "", 202

    return jsonify(responses if is_batch else responses[0])


@app.route("/health")
def health():
    """Liveness probe."""
    return jsonify({
        "status": "ok",
        "server": MCP_SERVER_NAME,
        "version": MCP_SERVER_VERSION,
        "tools": len(TOOLS),
    })


@app.route("/sse")
def sse():
    """
    SSE endpoint (legacy transport).

    The MCP client connects here first.  The server immediately sends an
    'endpoint' event that tells the client where to POST its messages.
    Subsequent JSON-RPC responses are pushed as 'message' events.
    """
    sid, q = _new_session()
    logger.info("SSE session opened: %s", sid)

    def generate():
        # Tell the client which URL to POST messages to
        endpoint_url = f"/messages?sessionId={sid}"
        yield f"event: endpoint\ndata: {endpoint_url}\n\n"

        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    if msg is None:          # sentinel: close the stream
                        break
                    payload = json.dumps(msg, ensure_ascii=False)
                    yield f"event: message\ndata: {payload}\n\n"
                except queue.Empty:
                    # Keep-alive comment
                    yield ": keepalive\n\n"
        finally:
            _remove_session(sid)
            logger.info("SSE session closed: %s", sid)

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/messages", methods=["POST"])
def messages():
    """
    JSON-RPC message endpoint (legacy SSE transport).

    The MCP client POSTs JSON-RPC requests here.  The server processes
    each request and pushes the response back via the SSE stream.
    Returns HTTP 202 Accepted immediately.
    """
    sid = request.args.get("sessionId", "")
    if not sid:
        return jsonify({"error": "Missing sessionId query parameter"}), 400

    with _sessions_lock:
        if sid not in _sessions:
            return jsonify({"error": "Session not found or expired"}), 404

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Handle both single messages and batches
    messages_list = body if isinstance(body, list) else [body]

    def process():
        for msg in messages_list:
            try:
                response = _handle_message(sid, msg)
                if response is not None:
                    _push(sid, response)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Unhandled error processing message: %s", msg)

    # Process in a background thread so we can return 202 immediately
    threading.Thread(target=process, daemon=True).start()

    return "", 202


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    logger.info("Starting %s v%s on %s:%s", MCP_SERVER_NAME, MCP_SERVER_VERSION, host, port)
    logger.info("Streamable HTTP (Joule Studio): POST /mcp")
    logger.info("SSE transport (Claude Desktop): GET /sse  POST /messages")
    logger.info("Health check:                   GET /health")
    logger.info("Tools available: %d", len(TOOLS))

    app.run(host=host, port=port, debug=debug, threaded=True)