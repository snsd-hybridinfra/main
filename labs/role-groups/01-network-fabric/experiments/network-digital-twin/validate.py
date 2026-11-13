#!/usr/bin/env python3
"""Validate reachability and resilience intents against a read-only graph model."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def enumerate_paths(adjacency: dict[str, set[str]], source: str, destination: str) -> list[list[str]]:
    paths: list[list[str]] = []

    def walk(current: str, path: list[str]) -> None:
        if current == destination:
            paths.append(path)
            return
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor not in path:
                walk(neighbor, [*path, neighbor])

    walk(source, [source])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.json")
    parser.add_argument("--evidence")
    args = parser.parse_args()

    model_path = Path(args.model)
    raw = model_path.read_bytes()
    model = json.loads(raw)
    denied = {
        (flow["source"], flow["destination"]): flow["reason"]
        for flow in model.get("denied_flows", [])
    }
    node_ids = {node["id"] for node in model["nodes"]}
    results = []

    for scenario in model["scenarios"]:
        disabled = set(scenario.get("disabled_nodes", []))
        adjacency = {node: set() for node in node_ids - disabled}
        for left, right in model["links"]:
            if left in adjacency and right in adjacency:
                adjacency[left].add(right)
                adjacency[right].add(left)

        checks = []
        for intent in scenario["checks"]:
            source = intent["source"]
            destination = intent["destination"]
            topology_paths = (
                enumerate_paths(adjacency, source, destination)
                if source in adjacency and destination in adjacency
                else []
            )
            policy_reason = denied.get((source, destination))
            effective_paths = [] if policy_reason else topology_paths
            reachable = bool(effective_paths)
            passed = reachable == intent["expected_reachable"]
            if "min_paths" in intent:
                passed = passed and len(effective_paths) >= intent["min_paths"]

            checks.append(
                {
                    "source": source,
                    "destination": destination,
                    "expected_reachable": intent["expected_reachable"],
                    "reachable": reachable,
                    "topology_path_count": len(topology_paths),
                    "effective_path_count": len(effective_paths),
                    "paths": topology_paths,
                    "policy_denied": bool(policy_reason),
                    "policy_reason": policy_reason,
                    "passed": passed,
                }
            )

        results.append(
            {
                "name": scenario["name"],
                "disabled_nodes": sorted(disabled),
                "checks": checks,
                "passed": all(check["passed"] for check in checks),
            }
        )

    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "model": model["model"],
        "model_sha256": hashlib.sha256(raw).hexdigest(),
        "sources": model.get("sources", []),
        "status": "passed" if all(item["passed"] for item in results) else "failed",
        "scenarios": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.evidence:
        Path(args.evidence).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
