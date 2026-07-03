"""
OAuth Setup Script for Kommo CRM
================================
Runs a local HTTP server, opens the browser for Kommo authorization,
and saves the tokens to .env automatically.
"""

from __future__ import annotations

import http.server
import os
import threading
import urllib.parse
import webbrowser

import httpx
from dotenv import load_dotenv, set_key

ENV_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_PATH)

CLIENT_ID = os.getenv("KOMMO_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("KOMMO_CLIENT_SECRET", "")
SUBDOMAIN = os.getenv("KOMMO_SUBDOMAIN", "")
REDIRECT_URI = os.getenv("KOMMO_REDIRECT_URI", "http://localhost:8080/callback")

PORT = int(urllib.parse.urlparse(REDIRECT_URI).port or 8080)

CONFIRM_HTML = """<!DOCTYPE html>
<html>
<head><title>Kommo MCP - Authorization</title></head>
<body style="font-family: system-ui; text-align: center; padding: 60px;">
  <h1>✅ Authorization Successful</h1>
  <p>Tokens saved to <code>.env</code>. You can close this window.</p>
  <p>Run <code>python -m kommo_mcp</code> to start the MCP server.</p>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html>
<head><title>Kommo MCP - Error</title></head>
<body style="font-family: system-ui; text-align: center; padding: 60px;">
  <h1>❌ Authorization Failed</h1>
  <p>{error}</p>
</body>
</html>"""


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    """Handle the OAuth callback."""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        code = params.get("code", [None])[0]
        if not code:
            self._respond(400, ERROR_HTML.format(error="No authorization code received"))
            return

        try:
            tokens = exchange_code(code)
            set_key(ENV_PATH, "KOMMO_ACCESS_TOKEN", tokens["access_token"])
            set_key(ENV_PATH, "KOMMO_REFRESH_TOKEN", tokens["refresh_token"])
            self._respond(200, CONFIRM_HTML)
            print("\n✅ Tokens saved successfully!")
            print("   Run: python -m kommo_mcp")
        except Exception as e:
            self._respond(500, ERROR_HTML.format(error=str(e)))
            print(f"\n❌ Error: {e}")

        # Shutdown server after response
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _respond(self, code: int, html: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: object) -> None:
        pass  # Suppress default logging


def exchange_code(code: str) -> dict:
    """Exchange authorization code for tokens."""
    resp = httpx.post(
        f"https://{SUBDOMAIN}.kommo.com/oauth2/access_token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    if not all([CLIENT_ID, CLIENT_SECRET, SUBDOMAIN]):
        print("❌ Missing credentials in .env file.")
        print("   Copy .env.example to .env and fill in your Kommo integration details.")
        return

    auth_url = (
        f"https://{SUBDOMAIN}.kommo.com/oauth"
        f"?client_id={CLIENT_ID}"
        f"&mode=post_message"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )

    print("🔐 Opening browser for Kommo authorization...")
    print(f"   If it doesn't open, visit: {auth_url}\n")
    webbrowser.open(auth_url)

    server = http.server.HTTPServer(("", PORT), OAuthHandler)
    print(f"⏳ Waiting for callback on port {PORT}...")
    server.serve_forever()


if __name__ == "__main__":
    main()
