"""Regression tests for the P1-ACC-001 superseding accepted-with-gaps decision."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_phase1_acceptance as acceptance  # noqa: E402


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Phase1AcceptanceTests(unittest.TestCase):
    def copied_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in acceptance.REQUIRED_PATHS:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return temporary, root

    def test_scoped_superseding_decision_is_valid(self) -> None:
        self.assertEqual([], acceptance.validate(ROOT))

    def test_unsupported_acceptance_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / acceptance.DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["decision"] = "ACCEPTED"
            write(path, value)
            self.assertTrue(acceptance.validate(root))
        finally:
            temporary.cleanup()

    def test_fresh_timestamp_cannot_support_stale_decision(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / acceptance.BLOCKED_DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["assessed_at"] = "2026-08-02T00:00:00Z"
            write(path, value)
            self.assertTrue(any("P7D expiration" in item or "STALE" in item for item in acceptance.validate(root)))
        finally:
            temporary.cleanup()

    def test_reopened_action_is_rejected_after_superseding_decision(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / acceptance.EXECUTION_PLAN
            value = json.loads(path.read_text(encoding="utf-8"))
            next(item for item in value["actions"] if item["action_id"] == "P1-ACC-001")["current_status"] = "BLOCKED"
            write(path, value)
            self.assertIn("P1-ACC-001 execution action must be COMPLETED by the superseding decision", acceptance.validate(root))
        finally:
            temporary.cleanup()

    def test_stale_evidence_cannot_be_reclassified(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / acceptance.DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["historical_freshness_state"]["reclassified_as_fresh"] = True
            write(path, value)
            self.assertTrue(any("freshness" in item.lower() or "superseding schema" in item for item in acceptance.validate(root)))
        finally:
            temporary.cleanup()

    def test_refresh_progress_cannot_overclaim_second_run(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / acceptance.REFRESH_PROGRESS
            value = json.loads(path.read_text(encoding="utf-8"))
            value["accepted_current_executions"] = 2
            write(path, value)
            self.assertTrue(any("refresh schema" in item or "refresh progress" in item for item in acceptance.validate(root)))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
