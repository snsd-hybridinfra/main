"""Offline, read-only duplicate IPv4 ARP claim detector for synthetic fixtures."""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address
import json
from pathlib import Path
import re

MAC = re.compile(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\Z")
REQUIRED = ("timestamp", "site", "vrf", "segment", "ip", "mac", "device", "vendor")


def stamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must have a timezone")
    return dt.astimezone(timezone.utc)


def normalize_claim(raw: dict) -> dict:
    if not all(isinstance(raw.get(key), str) and raw[key].strip() for key in REQUIRED):
        raise ValueError("claim missing required fields")
    claim = dict(raw)
    claim["timestamp"] = stamp(raw["timestamp"])
    claim["ip"] = str(IPv4Address(raw["ip"]))
    claim["mac"] = raw["mac"].lower()
    if not MAC.fullmatch(claim["mac"]):
        raise ValueError("MAC must be colon-delimited EUI-48")
    return claim


def key_of(item: dict) -> tuple[str, str, str, str]:
    return tuple(item[field] for field in ("site", "vrf", "segment", "ip"))


def detect(dataset: dict, window_seconds: int = 120) -> list[dict]:
    if window_seconds < 1:
        raise ValueError("window_seconds must be positive")
    baseline = {}
    for raw in dataset.get("gateway_baselines", []):
        key = key_of(raw)
        if key in baseline or not raw.get("allowed_macs"):
            raise ValueError("gateway baseline must be unique and nonempty")
        allowed = {mac.lower() for mac in raw["allowed_macs"]}
        if any(not MAC.fullmatch(mac) for mac in allowed):
            raise ValueError("invalid gateway baseline MAC")
        baseline[key] = allowed

    claims = sorted((normalize_claim(raw) for raw in dataset["observations"]
                     if raw.get("type") == "arp_claim"), key=lambda item: item["timestamp"])
    recent = defaultdict(deque)
    alerts = {}
    for claim in claims:
        key = key_of(claim)
        window = recent[key]
        while window and claim["timestamp"] - window[0]["timestamp"] > timedelta(seconds=window_seconds):
            window.popleft()
        window.append(claim)
        macs = {item["mac"] for item in window}
        if key in baseline:
            # Identity mismatch is not proof of a simultaneous live IP conflict.
            unexpected = macs - baseline[key]
            if not unexpected:
                continue
            event, severity = "GATEWAY_IP_UNEXPECTED_MAC", "critical"
        elif len(macs) > 1:
            event, severity = "IP_DUPLICATE_SUSPECTED", "warning"
        else:
            continue
        id_key = (key, event)
        active = alerts.get(id_key)
        observed = sorted(macs)
        if active is None:
            alerts[id_key] = {
                "event": event, "severity": severity, "status": "suspected",
                "site": key[0], "vrf": key[1], "segment": key[2], "ip": key[3],
                "macs": observed, "first_seen": window[0]["timestamp"].isoformat(),
                "last_seen": claim["timestamp"].isoformat(),
                "sources": sorted({item["device"] for item in window}),
            }
        else:
            active["macs"] = sorted(set(active["macs"]) | macs)
            active["last_seen"] = claim["timestamp"].isoformat()
            active["sources"] = sorted(set(active["sources"]) | {item["device"] for item in window})
    return sorted(alerts.values(), key=lambda a: (a["site"], a["vrf"], a["segment"], a["ip"], a["event"]))


def syslog(alert: dict) -> str:
    """Generate RFC 5424-style text locally; never transmit packets."""
    pri = 130 if alert["severity"] == "critical" else 132  # local0.crit / local0.warning
    message = (f'event={alert["event"]} status=suspected site={alert["site"]} '
               f'vrf={alert["vrf"]} segment={alert["segment"]} ip={alert["ip"]} '
               f'macs={",".join(alert["macs"])}')
    return f'<{pri}>1 {alert["last_seen"]} ipdup-lab arp-detector - {alert["event"]} - {message}'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--syslog-output", type=Path)
    parser.add_argument("--window-seconds", type=int, default=120)
    args = parser.parse_args()
    results = {"mode": "offline-synthetic", "window_seconds": args.window_seconds,
               "alerts": detect(json.loads(args.input.read_text(encoding="utf-8")), args.window_seconds)}
    body = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    if args.syslog_output:
        args.syslog_output.parent.mkdir(parents=True, exist_ok=True)
        args.syslog_output.write_text("\n".join(map(syslog, results["alerts"])) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
