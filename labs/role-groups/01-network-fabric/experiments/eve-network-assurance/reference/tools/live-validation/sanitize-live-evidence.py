#!/usr/bin/env python3
"""Create a separate sanitized copy of restricted live-validation output."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SAFE_IPV4 = {"192.168.1.30"}

PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.S), "<private-key-redacted>"),
    (re.compile(r"(?i)\b(?:password|passwd|token|secret|authorization|cookie|client_secret)\b\s*[:=]\s*[^\s]+"), "<credential-redacted>"),
    (re.compile(r"(?i)\b(?:OS_PASSWORD|OS_TOKEN|OS_AUTH_URL|AWS_SECRET_ACCESS_KEY|AZURE_CLIENT_SECRET)\s*=\s*[^\s]+"), "<credential-environment-redacted>"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"), "<uuid-redacted>"),
    (re.compile(r"(?i)\b(?:user|project)[_-]?id\b\s*[:=]\s*[^\s]+"), "<identity-id-redacted>"),
    (re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:])"), "<mac-address-redacted>"),
    (re.compile(r"(?i)(?:[A-Za-z]:[/\\]Users[/\\][^\s]+[/\\]\.ssh[/\\][^\s]+|/home/[^/\s]+/\.ssh/[^\s]+|/root/\.ssh/[^\s]+)"), "<ssh-path-redacted>"),
    (re.compile(r"(?i)/etc/(?:kolla/(?:clouds\.yaml|passwords\.yml)|shadow)"), "<sensitive-path-redacted>"),
    (re.compile(r"(?im)^\s*(?:enable\s+(?:password|secret)|password|secret|snmp-server\s+community)\s+\S+.*$"), "<cisco-secret-redacted>"),
    (re.compile(r"(?im)^\s*username\s+\S+.*(?:password|secret)\s+\S+.*$"), "<cisco-user-secret-redacted>"),
    (re.compile(r"(?i)\bconsole\s+port\s*[:=]\s*\d+"), "console port: <console-port-redacted>"),
)

IPV4_RE = re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b")


def sanitize(text: str) -> str:
    sanitized = text
    for pattern, replacement in PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    def replace_ip(match: re.Match[str]) -> str:
        value = match.group(0)
        return value if value in SAFE_IPV4 else "<runtime-ip-redacted>"

    return IPV4_RE.sub(replace_ip, sanitized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must be different files")
    if not args.input.is_file():
        parser.error("input file does not exist")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sanitize(args.input.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
