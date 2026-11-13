"""Regression and negative tests for the Stage B private-IaaS contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_private_iaas_golden_path as golden  # noqa: E402


def copy_authorities(target: Path) -> None:
    for relative in golden.REQUIRED_FILES:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


class PrivateIaasGoldenPathTests(unittest.TestCase):
    def test_current_contract_is_valid(self) -> None:
        result = golden.validate(ROOT)
        self.assertFalse(result.failures, result.failures)

    def test_live_authorization_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_authorities(target)
            path = target / golden.CONTRACT
            data = json.loads(path.read_text(encoding="utf-8"))
            data["deployment_authorized"] = True
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = golden.validate(target)
            self.assertTrue(any("does not authorize live deployment" in item for item in result.failures))

    def test_state_machine_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_authorities(target)
            path = target / golden.CONTRACT
            data = json.loads(path.read_text(encoding="utf-8"))
            data["state_machines"]["request"]["PENDING"].append("GRANTED")
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = golden.validate(target)
            self.assertTrue(any("request and Grant state machine" in item for item in result.failures))

    def test_catalog_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_authorities(target)
            path = target / Path("applications/internal-iaas-portal/terraform/catalog.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["deployment_authorized"] = True
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = golden.validate(target)
            self.assertTrue(any("source digest" in item or "defaults live deployment" in item for item in result.failures))

    def test_rollback_success_without_empty_state_proof_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_authorities(target)
            path = target / golden.CONTRACT
            data = json.loads(path.read_text(encoding="utf-8"))
            data["failure_recovery"]["success_claim_requires"] = "COMMAND_EXIT_ZERO"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = golden.validate(target)
            self.assertTrue(any("recovery remains fail-closed" in item for item in result.failures))


if __name__ == "__main__":
    unittest.main()
