#!/usr/bin/env python3
"""Generate a deterministic, non-executing ZT-AUTO-001 workflow plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from automation_common import ACTION_PATH, WORKFLOW_PATH, build_plan, load


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", default="ZTA-WF-VAL-001")
    parser.add_argument("--catalog", type=Path, default=WORKFLOW_PATH)
    parser.add_argument("--actions", type=Path, default=ACTION_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--mode", choices=("CHECK", "PLAN", "EXECUTE_READ_ONLY", "PROPOSAL_ONLY"), default="PLAN")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    try: plan = build_plan(args.workflow, args.mode, load(args.actions), load(args.catalog))
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {exc}"); return 1
    rendered = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.format == "json" or args.verbose: print(rendered)
    else: print(f"[PASS] workflow={plan['workflow_id']} mode={plan['execution_mode']} plan_hash={plan['plan_hash']} steps={len(plan['steps'])}")
    if args.verbose: print("[PASS] Deterministic plan generated; no action executed and no authority record modified.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
