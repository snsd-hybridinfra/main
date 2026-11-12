#!/usr/bin/env python3
"""Evaluate a ZT-AUTO-001 plan; this tool never runs actions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from automation_common import ACTION_PATH, POLICY_PATH, WORKFLOW_PATH, build_plan, load, policy_decision, unsafe_parameters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", default="ZTA-WF-VAL-001")
    parser.add_argument("--mode", choices=("CHECK", "PLAN", "EXECUTE_READ_ONLY", "PROPOSAL_ONLY"), default="CHECK")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--parameters", default="{}")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    try:
        parameters = json.loads(args.parameters)
        if not isinstance(parameters, dict): raise ValueError("Parameters must be an object")
        unsafe = unsafe_parameters(parameters)
        if unsafe:
            for item in unsafe: print(f"[FAIL] {item}")
            return 1
        actions, workflows = load(ACTION_PATH), load(WORKFLOW_PATH)
        load(POLICY_PATH)
        plan = build_plan(args.workflow, args.mode, actions, workflows)
        approval = load(args.approval) if args.approval else None
        decision, reasons = policy_decision(plan, args.mode, approval)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}"); return 1
    level = "PASS" if decision.startswith("ALLOW_") else "WARN" if decision == "REQUIRE_APPROVAL" else "FAIL"
    print(f"[{level}] decision={decision} workflow={args.workflow} mode={args.mode} risk={plan['effective_risk']} plan_hash={plan['plan_hash']}")
    for reason in reasons: print(f"[{level}] {reason}")
    if args.verbose: print("[PASS] Policy evaluation performed no action.")
    return 0 if level != "FAIL" else 1


if __name__ == "__main__": raise SystemExit(main())
