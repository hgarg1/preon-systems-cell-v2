"""One-time script to obtain a Gmail OAuth2 refresh token for transactional email.

Usage:
    python -m preon_systems_cell.email_setup

It will open a browser for the Google consent screen, then print the refresh token
to paste into GOOGLE_REFRESH_TOKEN in your .env file.

Requires: pip install google-auth-oauthlib  (or: pip install 'preon-systems-cell[email]')
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except ImportError:
    pass
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:9876/callback"
SCOPES = "https://mail.google.com/"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_code: str | None = None


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _code
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            _code = params.get("code", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding:3rem'><h2>Authorization complete - close this tab.</h2></body></html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env first.")
        sys.exit(1)

    auth_url = (
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code"
        f"&scope={urllib.parse.quote(SCOPES)}"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    print("Opening browser for Google consent…")
    print(f"\nIf the browser does not open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 9876), _Handler)
    server.handle_request()

    if not _code:
        print("No authorization code received.")
        sys.exit(1)

    token_data = urllib.parse.urlencode({
        "code": _code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    with urllib.request.urlopen(TOKEN_URL, data=token_data, timeout=15) as resp:
        tokens = json.loads(resp.read())

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print(f"No refresh_token in response. Full response:\n{json.dumps(tokens, indent=2)}")
        sys.exit(1)

    print("\nSuccess! Add these to your .env file:\n")
    print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
    print(f"GOOGLE_OAUTH_EMAIL=<the Gmail address you just authorized>")


if __name__ == "__main__":
    main()
