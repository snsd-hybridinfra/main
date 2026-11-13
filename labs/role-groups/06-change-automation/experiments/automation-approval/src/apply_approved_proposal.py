#!/usr/bin/env python3
"""Validate or show a proposal diff; automatic repository writes do not exist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from automation_common import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--show-diff", action="store_true")
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    try:
        path = args.proposal.resolve()
        boundary = (ROOT / ".runtime/zero-trust/automation/proposals").resolve()
        path.relative_to(boundary)
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("authoritative_update_performed") is not False: raise ValueError("Proposal claims an authoritative update")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}"); return 1
    print("[PASS] Proposal is bounded to ignored runtime and requires human review.")
    if args.show_diff: print("[WARN] No authoritative diff is generated because automatic write mode is intentionally absent.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
