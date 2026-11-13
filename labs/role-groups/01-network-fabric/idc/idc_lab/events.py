"""Send correlated RFC 5424 messages to the lab's Alloy receiver."""
import json
import re
import socket
from uuid import uuid4

from .model import STATE
from .verify import utc, write_json

SYSLOG = ("127.0.0.1", 1514)
CHANGE_DIR = STATE / "change-events"
FRR_LINE = re.compile(r"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d(?:\.\d+)?) (.+)")


def emit(node, app, message, timestamp=None):
    wire = f"<134>1 {timestamp or utc()} {node} {app} - - - {message}".encode()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.sendto(wire, SYSLOG)
    except OSError:
        # Local report generation also works with the optional receiver down.
        pass


def event(name, **fields):
    record = {"timestamp": utc(), "event": name, **fields}
    emit("idc-lab", "operator", json.dumps(record, ensure_ascii=False), record["timestamp"])
    return record


def change_event(name, **fields):
    """Keep a local change record even when Syslog is unavailable."""
    record = {"timestamp": utc(), "event": name, **fields}
    CHANGE_DIR.mkdir(mode=0o700, exist_ok=True)
    write_json(CHANGE_DIR / (uuid4().hex + ".json"), record)
    emit("idc-lab", "operator", json.dumps(record), record["timestamp"])
    return record
