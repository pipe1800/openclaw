#!/usr/bin/env python3
"""
Google OAuth2 Helper - Handles token generation and refresh with localhost redirect.

Usage:
    # First time: Start local auth server and open browser
    python google_auth.py login --client-id <id> --client-secret <secret>

    # Refresh access token
    python google_auth.py refresh --client-id <id> --client-secret <secret> --refresh-token <token>

    # Get access token (refreshes automatically)
    python google_auth.py token --client-id <id> --client-secret <secret> --refresh-token <token>

Environment Variables:
    GOOGLE_CLIENT_ID     - OAuth2 client ID
    GOOGLE_CLIENT_SECRET - OAuth2 client secret
    GOOGLE_REFRESH_TOKEN - Refresh token (after initial auth)
"""

import argparse
import json
import os
import sys
import webbrowser
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.error import HTTPError
import threading

# Scopes for Drive, Calendar, and Meet
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]

REDIRECT_PORT = 8089
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback."""
    
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_GET(self):
        """Handle the OAuth callback."""
        parsed = urlparse(self.path)
        
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            
            if "code" in params:
                self.server.auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    </body></html>
                """)
            elif "error" in params:
                self.server.auth_error = params.get("error_description", params["error"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<html><body><h1>Error</h1><p>{self.server.auth_error}</p></body></html>".encode())
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def get_auth_url(client_id):
    """Generate authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code(client_id, client_secret, code):
    """Exchange authorization code for tokens."""
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    
    req = Request(
        "https://oauth2.googleapis.com/token",
        data=urlencode(data).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        error = e.read().decode()
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


def refresh_access_token(client_id, client_secret, refresh_token):
    """Refresh access token using refresh token."""
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    
    req = Request(
        "https://oauth2.googleapis.com/token",
        data=urlencode(data).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        error = e.read().decode()
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


def run_auth_flow(client_id, client_secret):
    """Run the full OAuth flow with local server."""
    # Start local server
    server = HTTPServer(("localhost", REDIRECT_PORT), OAuthCallbackHandler)
    server.auth_code = None
    server.auth_error = None
    
    # Generate and open auth URL
    auth_url = get_auth_url(client_id)
    print(f"Opening browser for authorization...")
    print(f"If browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization...")
    while server.auth_code is None and server.auth_error is None:
        server.handle_request()
    
    server.server_close()
    
    if server.auth_error:
        print(f"Authorization failed: {server.auth_error}", file=sys.stderr)
        sys.exit(1)
    
    # Exchange code for tokens
    print("Exchanging code for tokens...")
    tokens = exchange_code(client_id, client_secret, server.auth_code)
    
    return tokens


def main():
    parser = argparse.ArgumentParser(description="Google OAuth2 Helper")
    subparsers = parser.add_subparsers(dest="command")
    
    # login command - full OAuth flow
    p = subparsers.add_parser("login", help="Run OAuth login flow")
    p.add_argument("--client-id", default=os.environ.get("GOOGLE_CLIENT_ID"))
    p.add_argument("--client-secret", default=os.environ.get("GOOGLE_CLIENT_SECRET"))
    
    # refresh command
    p = subparsers.add_parser("refresh", help="Refresh access token")
    p.add_argument("--client-id", default=os.environ.get("GOOGLE_CLIENT_ID"))
    p.add_argument("--client-secret", default=os.environ.get("GOOGLE_CLIENT_SECRET"))
    p.add_argument("--refresh-token", default=os.environ.get("GOOGLE_REFRESH_TOKEN"))
    
    # token command - just get access token
    p = subparsers.add_parser("token", help="Get access token (refreshes if needed)")
    p.add_argument("--client-id", default=os.environ.get("GOOGLE_CLIENT_ID"))
    p.add_argument("--client-secret", default=os.environ.get("GOOGLE_CLIENT_SECRET"))
    p.add_argument("--refresh-token", default=os.environ.get("GOOGLE_REFRESH_TOKEN"))
    
    args = parser.parse_args()
    
    if args.command == "login":
        if not all([args.client_id, args.client_secret]):
            print("Error: --client-id and --client-secret required", file=sys.stderr)
            sys.exit(1)
        
        tokens = run_auth_flow(args.client_id, args.client_secret)
        print("\n" + "="*50)
        print("[OK] Authorization successful!")
        print("="*50)
        print(json.dumps(tokens, indent=2))
        print("\n[!] Save the refresh_token above! Add it to TOOLS.md or environment.")
        
        if "refresh_token" in tokens:
            print(f"\nRefresh Token:\n{tokens['refresh_token']}")
    
    elif args.command == "refresh":
        if not all([args.client_id, args.client_secret, args.refresh_token]):
            print("Error: client-id, client-secret, and refresh-token required", file=sys.stderr)
            sys.exit(1)
        tokens = refresh_access_token(args.client_id, args.client_secret, args.refresh_token)
        print(json.dumps(tokens, indent=2))
    
    elif args.command == "token":
        if not all([args.client_id, args.client_secret, args.refresh_token]):
            print("Error: client-id, client-secret, and refresh-token required", file=sys.stderr)
            sys.exit(1)
        tokens = refresh_access_token(args.client_id, args.client_secret, args.refresh_token)
        # Just output the access token for piping
        print(tokens["access_token"])
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
