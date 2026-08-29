from __future__ import annotations

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: install websockets with 'python -m pip install websockets'.") from exc

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8765"))
DERIV_WS_URL = "wss://ws.deriv.com/websockets/v3"


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    content_length = int(handler.headers.get("Content-Length", "0") or "0")
    raw_body = handler.rfile.read(content_length).decode("utf-8")
    if not raw_body.strip():
        return {}
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        raise ValueError("Request body must be valid JSON.")


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


async def authorize_deriv(app_id: str, access_token: str) -> dict:
    if not app_id or not access_token:
        return {
            "connected": False,
            "error": "Missing Deriv app ID or access token.",
        }

    try:
        uri = f"{DERIV_WS_URL}?app_id={app_id}"
        async with websockets.connect(uri, ping_interval=None, timeout=15) as websocket:
            await websocket.send(json.dumps({"authorize": access_token}))
            auth_reply = json.loads(await websocket.recv())

            if auth_reply.get("error"):
                return {
                    "connected": False,
                    "error": auth_reply.get("error", {}).get("message", "Authorization failed."),
                }

            if auth_reply.get("authorize"):
                return {
                    "connected": True,
                    "message": "Deriv account authorized successfully.",
                    "account": auth_reply.get("authorize", {}).get("loginid"),
                    "environment": "real" if str(app_id) not in {"1089", "16929"} else "demo",
                }

            return {
                "connected": False,
                "error": "Authorization response did not include account details.",
            }
    except Exception as exc:  # pragma: no cover - depends on network and credentials
        return {
            "connected": False,
            "error": f"Unable to connect to Deriv: {exc}",
        }


class DerivHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/deriv/health":
            send_json(self, 200, {"status": "ok", "service": "deriv-connector"})
            return

        send_json(self, 404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/deriv/connect":
            try:
                payload = read_json_body(self)
            except ValueError as exc:
                send_json(self, 400, {"connected": False, "error": str(exc)})
                return

            app_id = str(payload.get("appId", "")).strip()
            access_token = str(payload.get("accessToken", "")).strip()
            environment = str(payload.get("environment", "real")).strip().lower()

            if app_id and access_token:
                try:
                    result = asyncio.run(authorize_deriv(app_id, access_token))
                    if environment == "demo":
                        result["environment"] = "demo"
                    send_json(self, 200 if result.get("connected") else 401, result)
                    return
                except Exception as exc:  # pragma: no cover
                    send_json(self, 500, {"connected": False, "error": str(exc)})
                    return

            send_json(self, 400, {"connected": False, "error": "Provide both appId and accessToken."})
            return

        send_json(self, 404, {"error": "Not found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), DerivHandler)
    print(f"Deriv connector running on http://{HOST}:{PORT}")
    server.serve_forever()
