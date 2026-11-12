"""Send correlated RFC 5424 messages to the lab's Alloy receiver."""
import json
import socket

from .verify import utc

SYSLOG = ("127.0.0.1", 1514)


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
