#!/usr/bin/env python3
"""Validate the ZT-VIS-002 proxy over an SSH command-channel transport."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shlex
import socket
import ssl
import stat
import subprocess
import threading
from pathlib import Path


def protected_file(path: Path) -> None:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError(f"protected input is missing or has an unsafe mode: {path.name}")


def inventory_values(path: Path) -> tuple[str, str, Path, Path, Path]:
    text = path.read_text(encoding="utf-8")
    target_match = re.search(r'ansible_host:\s*"([0-9.]+)"', text)
    proxy_match = re.search(r'ubuntu@([0-9.]+)"', text)
    target_key_match = re.search(r'ansible_ssh_private_key_file:\s*"([^"]+)"', text)
    known_match = re.search(r'UserKnownHostsFile=([^\s]+)', text)
    proxy_key_match = re.search(r'ProxyCommand="ssh -i ([^\s]+)', text)
    if not all((target_match, proxy_match, target_key_match, known_match, proxy_key_match)):
        raise ValueError("inventory does not contain the reviewed restricted SSH path")
    return (
        target_match.group(1),
        proxy_match.group(1),
        Path(target_key_match.group(1)),
        Path(proxy_key_match.group(1)),
        Path(known_match.group(1)),
    )


def exchange(
    ssh_args: list[str],
    context: ssl.SSLContext,
    server_name: str,
    request: bytes,
) -> tuple[int | None, bool]:
    process = subprocess.Popen(
        ssh_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )
    wire, tls_side = socket.socketpair()
    wire.settimeout(15)
    tls_side.settimeout(15)

    def to_ssh() -> None:
        try:
            while data := wire.recv(65536):
                process.stdin.write(data)
                process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    def from_ssh() -> None:
        try:
            while data := process.stdout.read(65536):
                wire.sendall(data)
        except OSError:
            pass
        finally:
            try:
                wire.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    for worker in (to_ssh, from_ssh):
        threading.Thread(target=worker, daemon=True).start()
    status_code: int | None = None
    rejected = False
    try:
        with context.wrap_socket(tls_side, server_hostname=server_name) as connection:
            connection.sendall(request)
            response = bytearray()
            while data := connection.recv(65536):
                response.extend(data)
            first_line = bytes(response).split(b"\r\n", 1)[0]
            matched = re.match(rb"HTTP/\d(?:\.\d)?\s+(\d{3})", first_line)
            status_code = int(matched.group(1)) if matched else None
    except (ssl.SSLError, ConnectionError, TimeoutError, OSError):
        rejected = True
    finally:
        try:
            wire.close()
        except OSError:
            pass
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    return status_code, rejected


def validate(args: argparse.Namespace) -> dict[str, str]:
    inventory = Path(args.inventory).resolve()
    ca = Path(args.ca).resolve()
    client_certificate = Path(args.client_certificate).resolve()
    client_key = Path(args.client_key).resolve()
    for path in (inventory, ca, client_certificate, client_key):
        protected_file(path)
    target, proxy, target_key, proxy_key, known_hosts = inventory_values(inventory)
    for path in (target_key, proxy_key, known_hosts):
        protected_file(path)

    proxy_command = (
        f"ssh -i {proxy_key} -T -o BatchMode=yes -o IdentitiesOnly=yes "
        f"-o StrictHostKeyChecking=yes -o UserKnownHostsFile={known_hosts} "
        f"-p 22 ubuntu@{proxy}"
    )
    remote = "bash -c " + shlex.quote(
        f"exec 3<>/dev/tcp/{target}/443; cat <&3 & cat >&3; wait"
    )
    ssh_args = [
        "ssh", "-T", "-i", str(target_key),
        "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={known_hosts}",
        "-o", f"ProxyCommand={proxy_command}", f"ubuntu@{target}", remote,
    ]

    plain_context = ssl.create_default_context(cafile=str(ca))
    request = (
        f"GET /api/health HTTP/1.1\r\nHost: {args.server_name}\r\n"
        "Connection: close\r\n\r\n"
    ).encode()
    no_client_status, no_client_rejected = exchange(
        ssh_args, plain_context, args.server_name, request
    )
    no_client_denied = no_client_rejected or no_client_status in {400, 401, 403, 495, 496}

    client_context = ssl.create_default_context(cafile=str(ca))
    client_context.load_cert_chain(str(client_certificate), str(client_key))
    approved_status, _ = exchange(ssh_args, client_context, args.server_name, request)

    false_basic = base64.b64encode(b"validator-denied:known-false-value").decode("ascii")
    denied_request = (
        f"GET /api/user HTTP/1.1\r\nHost: {args.server_name}\r\n"
        f"Authorization: Basic {false_basic}\r\nConnection: close\r\n\r\n"
    ).encode()
    denied_status, _ = exchange(ssh_args, client_context, args.server_name, denied_request)
    result = {
        "mtls_without_client": "REJECTED" if no_client_denied else "FAIL",
        "mtls_with_approved_client": "PASS" if approved_status == 200 else "FAIL",
        "grafana_false_basic": "REJECTED" if denied_status == 401 else "FAIL",
    }
    if "FAIL" in result.values():
        raise RuntimeError(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--client-certificate", required=True)
    parser.add_argument("--client-key", required=True)
    parser.add_argument("--server-name", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args), sort_keys=True))
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"validation": "FAIL", "reason": type(error).__name__}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
