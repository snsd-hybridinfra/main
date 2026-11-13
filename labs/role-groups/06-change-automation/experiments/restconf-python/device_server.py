#!/usr/bin/env python3
"""Small read-only HTTPS endpoint that mimics one IOS XE RESTCONF resource."""
import base64
import hmac
import json
import os
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENDPOINT = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
PAYLOAD = json.loads(Path("/opt/mock/fixtures/interfaces.json").read_text(encoding="utf-8"))
USER = os.environ["IOSXE_MOCK_USER"]
PASSWORD = os.environ["IOSXE_MOCK_PASSWORD"]
EXPECTED = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path != ENDPOINT:
            self.send_error(404)
            return
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied, EXPECTED):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="synthetic-iosxe"')
            self.end_headers()
            return
        body = json.dumps(PAYLOAD).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/yang-data+json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


server = HTTPServer(("0.0.0.0", 443), Handler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("/run/mock/device.crt", "/run/mock/device.key")
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()
