"""Tests for the package-oriented Phase 1 runbook validator."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_phase1_runbook_baseline as validator  # noqa: E402


class RunbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "docs" / "runbooks", self.root / "docs" / "runbooks")
        (self.root / "docs" / "zero-trust").mkdir(parents=True)
        shutil.copy2(ROOT / validator.FLOW_PATH, self.root / validator.FLOW_PATH)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def failures(self) -> list[validator.Finding]:
        return [item for item in validator.run_validation(self.root) if item.level == "FAIL"]

    def test_current_manifest_passes(self) -> None:
        self.assertEqual([], self.failures())

    def test_phase_completion_overclaim_fails(self) -> None:
        path = self.root / validator.MANIFEST_PATH
        data = json.loads(path.read_text(encoding="utf-8"))
        data["phase_state"]["completion_status"] = "COMPLETE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any(item.category == "phase" for item in self.failures()))

    def test_unknown_package_fails(self) -> None:
        path = self.root / validator.MANIFEST_PATH
        data = json.loads(path.read_text(encoding="utf-8"))
        data["runbooks"][0]["related_packages"] = ["ZT-UNKNOWN-001"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any(item.category == "packages" for item in self.failures()))

    def test_missing_runbook_fails(self) -> None:
        (self.root / next(iter(validator.REQUIRED_RUNBOOKS.values()))).unlink()
        self.assertTrue(any(item.category == "files" for item in self.failures()))


if __name__ == "__main__":
    unittest.main()
