"""Repository-safety regression tests for package-oriented validation."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts):
        if "__pycache__" in path.parts:
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class RepositoryValidationHygieneTests(unittest.TestCase):
    def test_retirement_validator_is_read_only(self) -> None:
        before = fingerprint()
        result = subprocess.run(
            [sys.executable, "tools/validate_scenario_retirement.py"], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        after = fingerprint()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, after)

    def test_package_flow_has_no_duplicate_ids(self) -> None:
        import json
        flow = json.loads((ROOT / "docs/zero-trust/package-flow.yaml").read_text(encoding="utf-8"))
        package_ids = [item["package_id"] for item in flow["packages"]]
        self.assertEqual(len(package_ids), len(set(package_ids)))
        self.assertEqual("ZT-RV-001", flow["phase_1_acceptance"]["scope_boundary"])
        self.assertEqual("ZT-SCH-001", flow["deferred_final_work"]["package_id"])
        self.assertEqual("DISABLED", flow["deferred_final_work"]["schedule_state"])
        self.assertEqual("COMPLETED_WITH_GAPS", flow["phase_1_acceptance"]["completion_status"])
        self.assertEqual("ACCEPTED_WITH_GAPS", flow["phase_1_acceptance"]["decision_status"])
        self.assertIsNone(flow["phase_1_acceptance"]["blocking_reason"])
        self.assertEqual("P1-RV-FRESHNESS-001", flow["phase_1_acceptance"]["accepted_exception"])
        self.assertEqual("STALE_RV_EVIDENCE", flow["phase_1_acceptance"]["deferred_final_risk"])


if __name__ == "__main__":
    unittest.main()
