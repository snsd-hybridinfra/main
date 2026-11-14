#!/usr/bin/env python3
"""Detect one synthetic credential in local log and process-argument samples."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="credential-exposure-cases.json")
    parser.add_argument("--evidence")
    args = parser.parse_args()

    input_path = Path(args.input)
    raw = input_path.read_bytes()
    data = json.loads(raw)
    marker = data["synthetic_secret"]
    marker_hex = marker.encode().hex()
    results = []

    for case in data["cases"]:
        text = case["text"]
        encodings = []
        if marker in text:
            encodings.append("raw")
        if marker_hex.lower() in text.lower():
            encodings.append("hex")
        exposed = bool(encodings)
        results.append({
            "name": case["name"],
            "surface": case["surface"],
            "expected_exposed": case["expected_exposed"],
            "actual_exposed": exposed,
            "detected_encodings": encodings,
            "passed": exposed == case["expected_exposed"],
        })

    passed = all(item["passed"] for item in results)
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "source": data["source"],
        "scope": "synthetic local log and process-argument samples",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "summary": {
            "total": len(results),
            "passed": sum(item["passed"] for item in results),
            "exposures_detected": sum(item["actual_exposed"] for item in results),
        },
        "results": results,
        "not_validated": [
            "Amazon Kinesis Producer Library runtime or affected package versions",
            "AWS credential issuance, use, revocation, or rotation",
            "host process visibility, log pipeline, or third-party secret scanners",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.evidence:
        Path(args.evidence).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
