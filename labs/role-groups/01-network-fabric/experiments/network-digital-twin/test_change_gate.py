#!/usr/bin/env python3
"""Run a synthetic pre/post network change gate without production access."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path


SOURCE = {
    "url": "https://aws.amazon.com/about-aws/whats-new/2026/11/interconnect-last-mile-preview-equinix/",
    "published_at": "2026-11-04",
}


def paths(links, source, destination):
    adjacency = defaultdict(set)
    for left, right in links:
        adjacency[left].add(right)
        adjacency[right].add(left)

    found = []

    def walk(node, visited):
        if node == destination:
            found.append(visited)
            return
        for next_node in sorted(adjacency[node] - set(visited)):
            walk(next_node, visited + [next_node])

    walk(source, [source])
    return found


def effective_count(topology_paths, source, destination, denied):
    return 0 if (source, destination) in denied else len(topology_paths)


def evaluate(links, denied, established_bgp_sessions):
    client_paths = paths(links, "client", "app")
    guest_paths = paths(links, "guest", "admin")
    return {
        "established_bgp_sessions": established_bgp_sessions,
        "client_app_topology_paths": len(client_paths),
        "client_app_effective_paths": effective_count(
            client_paths, "client", "app", denied
        ),
        "guest_admin_topology_paths": len(guest_paths),
        "guest_admin_effective_paths": effective_count(
            guest_paths, "guest", "admin", denied
        ),
    }


def run_cases():
    base_links = [
        ("client", "leaf1"),
        ("guest", "leaf1"),
        ("leaf1", "spine1"),
        ("leaf1", "spine2"),
        ("spine1", "leaf2"),
        ("spine2", "leaf2"),
        ("leaf2", "app"),
        ("leaf2", "admin"),
    ]
    segmentation = {("guest", "admin")}
    cases = {
        "baseline": (base_links, segmentation, 2, True),
        "spine1_link_removed": (
            [edge for edge in base_links if edge != ("leaf1", "spine1")],
            segmentation,
            1,
            False,
        ),
        "service_policy_blocks_app": (
            base_links,
            segmentation | {("client", "app")},
            2,
            False,
        ),
        "segmentation_removed": (base_links, set(), 2, False),
        "restored": (base_links, segmentation, 2, True),
    }

    results = {}
    for name, (links, denied, sessions, expected_accept) in cases.items():
        observed = evaluate(links, denied, sessions)
        actual_accept = (
            observed["established_bgp_sessions"] == 2
            and observed["client_app_effective_paths"] >= 2
            and observed["guest_admin_effective_paths"] == 0
        )
        results[name] = {
            "observed": observed,
            "expected_accept": expected_accept,
            "actual_accept": actual_accept,
            "passed": actual_accept == expected_accept,
        }

    passed = sum(result["passed"] for result in results.values())
    accepted = sum(result["actual_accept"] for result in results.values())
    return {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed == len(results) else "failed",
        "source": SOURCE,
        "scope": "synthetic undirected graph, session count, and pair policy only",
        "summary": {
            "total": len(results),
            "passed": passed,
            "accepted": accepted,
            "rejected": len(results) - accepted,
        },
        "results": results,
        "not_validated": [
            "AWS Interconnect, Direct Connect, Equinix, or MACsec runtime",
            "BGP protocol negotiation, route selection, or convergence time",
            "VLAN, ASN, physical circuit diversity, or service SLA",
            "ACL order, ports, protocols, latency, loss, or application probes",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    evidence = run_cases()
    rendered = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    print(rendered, end="")
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(rendered, encoding="utf-8")
    if evidence["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
