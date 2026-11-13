#!/usr/bin/env python3
"""Tiny loopback-only SQLite-backed synthetic service for recovery testing."""
import argparse
import json
from contextlib import closing
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.execute(
        "CREATE TABLE IF NOT EXISTS events "
        "(seq INTEGER PRIMARY KEY AUTOINCREMENT, at_utc TEXT NOT NULL, value TEXT NOT NULL)"
    )
    db.commit()
    return db


def handler_for(db_path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/health":
                return self.respond(404, {"error": "not found"})
            with closing(connect(db_path)) as db:
                count, last = db.execute(
                    "SELECT COUNT(*), COALESCE(MAX(seq), 0) FROM events"
                ).fetchone()
            self.respond(200, {"ok": True, "count": count, "last_seq": last})

        def do_POST(self):
            if self.path != "/events":
                return self.respond(404, {"error": "not found"})
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 1024:
                return self.respond(400, {"error": "invalid size"})
            try:
                value = json.loads(self.rfile.read(size))["value"]
                if not isinstance(value, str) or len(value) > 100:
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                return self.respond(400, {"error": "invalid event"})
            with closing(connect(db_path)) as db:
                cursor = db.execute(
                    "INSERT INTO events (at_utc, value) VALUES (?, ?)",
                    (datetime.now(timezone.utc).isoformat(), value),
                )
                seq = cursor.lastrowid
                db.commit()
            self.respond(201, {"seq": seq})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(args.db)) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
