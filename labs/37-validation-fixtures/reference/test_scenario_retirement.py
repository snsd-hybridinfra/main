"""Regression tests for the numbered-scenario retirement authority."""

from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_scenario_retirement as validator  # noqa: E402


class ScenarioRetirementTests(unittest.TestCase):
    def test_repository_retirement_passes(self) -> None:
        result = validator.run(ROOT)
        self.assertEqual([], [item for item in result.findings if item.level == "FAIL"])

    def test_numbered_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scenarios").mkdir()
            result = validator.Result()
            validator.validate_retired_paths(root, result)
            self.assertEqual(1, result.failed)

    def test_active_numbered_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "active.md"
            path.write_text("Use S" + "001 as current authority.\n", encoding="utf-8")
            result = validator.Result()
            validator.validate_references(root, [Path("active.md")], result)
            self.assertEqual(1, result.failed)

    def test_migration_record_reference_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / validator.MIGRATION_DOC
            path.parent.mkdir(parents=True)
            path.write_text("S" + "001-S" + "050 were retired.\n", encoding="utf-8")
            result = validator.Result()
            validator.validate_references(root, [validator.MIGRATION_DOC], result)
            self.assertEqual(0, result.failed)

    def test_duplicate_package_flow_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in (validator.FLOW_PATH, validator.FLOW_SCHEMA):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            import json
            flow_path = root / validator.FLOW_PATH
            flow = json.loads(flow_path.read_text(encoding="utf-8"))
            flow["phase_1_sequence"][1] = flow["phase_1_sequence"][0]
            flow_path.write_text(json.dumps(flow), encoding="utf-8")
            result = validator.Result()
            validator.validate_flow(root, result)
            self.assertGreater(result.failed, 0)


if __name__ == "__main__":
    unittest.main()
