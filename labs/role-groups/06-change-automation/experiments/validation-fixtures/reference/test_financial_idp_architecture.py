"""Regression tests for the Financial Hybrid-Ready IDP authority."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_financial_idp_architecture as architecture  # noqa: E402


class FinancialIdpArchitectureTests(unittest.TestCase):
    def test_current_architecture_is_valid(self) -> None:
        result = architecture.validate(ROOT)
        self.assertFalse(result.failures, result.failures)

    def test_active_hybrid_cloud_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for relative in architecture.REQUIRED_FILES:
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            baseline_path = target / architecture.BASELINE
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline["project"]["operating_claim"] = "HYBRID_OPERATIONAL"
            baseline["truth_boundaries"]["active_hybrid_cloud"] = True
            baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
            result = architecture.validate(target)
            self.assertTrue(any("Hybrid-Ready" in item or "active_hybrid_cloud" in item for item in result.failures))

    def test_network_runtime_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for relative in architecture.REQUIRED_FILES:
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            baseline_path = target / architecture.BASELINE
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            network = next(item for item in baseline["layers"] if item["name"] == "FINANCIAL_NETWORK")
            network["status"] = "RUNTIME_VALIDATED"
            baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
            result = architecture.validate(target)
            self.assertTrue(any("FINANCIAL_NETWORK" in item for item in result.failures))

    def test_real_securities_connectivity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for relative in architecture.REQUIRED_FILES:
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            baseline_path = target / architecture.BASELINE
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline["truth_boundaries"]["real_market_connectivity"] = True
            baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
            result = architecture.validate(target)
            self.assertTrue(any("real_market_connectivity" in item for item in result.failures))

    def test_aws_activation_by_file_presence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for relative in architecture.REQUIRED_FILES:
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            inventory_path = target / architecture.INVENTORY
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["assets"].append(
                {
                    "path": "platform/infra/aws/",
                    "disposition": "ACTIVE",
                    "owner": "UNOWNED",
                    "reason": "test mutation",
                    "required_work": [],
                }
            )
            inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
            result = architecture.validate(target)
            self.assertTrue(any("platform/infra/aws/" in item for item in result.failures))


if __name__ == "__main__":
    unittest.main()
