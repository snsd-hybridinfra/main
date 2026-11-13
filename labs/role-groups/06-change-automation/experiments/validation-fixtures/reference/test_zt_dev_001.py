"""Regression tests for the bounded ZT-DEV-001 package."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


COLLECTOR = _load_module("zt_dev_collector", REPO_ROOT / "tools/endpoint/collect_software_inventory.py")
VALIDATOR = _load_module("zt_dev_validator", REPO_ROOT / "tools/endpoint/validate_endpoint_compliance.py")


class ZtDev001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads((REPO_ROOT / "docs/zero-trust/device/device-inventory.yaml").read_text(encoding="utf-8"))
        self.policy = json.loads((REPO_ROOT / "docs/zero-trust/device/endpoint-compliance-policy.yaml").read_text(encoding="utf-8"))
        self.now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
        self.raw = {
            "asset_id": "ZTD-ASSET-MONITORING-VM-01",
            "collection_time": "2026-07-22T11:30:00Z",
            "source_authority": "SYNTHETIC_FIXTURE",
            "os_family": "ubuntu",
            "os_release": "24.04",
            "kernel": "fixture-kernel",
            "package_count": 10,
            "container_runtime": "fixture-runtime",
            "compose_runtime": "fixture-compose",
            "running_container_count": 3,
            "security_updates_available": 0,
            "reboot_required": False,
            "package_manager_error": False,
            "endpoint_agent_state": "NOT_INSTALLED",
        }
        self.evidence = COLLECTOR.normalize_record(self.raw)
        self.evidence["vulnerability"]["classification"] = "ASSESSED_NO_BLOCKING_FINDING"

    def _findings(self, inventory=None, policy=None, evidence=None):
        findings, counts = VALIDATOR.validate_package(
            inventory or self.inventory,
            policy or self.policy,
            [self.evidence] if evidence is None else evidence,
            now=self.now,
        )
        return findings, counts

    def _assert_failure(self, check: str, inventory=None, policy=None, evidence=None) -> None:
        findings, _ = self._findings(inventory, policy, evidence)
        self.assertTrue(any(item.level == "FAIL" and item.check == check for item in findings), findings)

    def test_collector_normalizes_read_only_record(self) -> None:
        value = COLLECTOR.normalize_record(self.raw)
        self.assertEqual("CURRENT", value["patch_state"]["classification"])
        self.assertFalse(value["patch_state"]["automatic_patching_performed"])
        self.assertFalse(value["vulnerability"]["exploit_executed"])

    def test_collector_rejects_unexpected_field(self) -> None:
        raw = dict(self.raw, password="fixture")
        with self.assertRaises(ValueError):
            COLLECTOR.normalize_record(raw)

    def test_valid_fixture_passes(self) -> None:
        findings, counts = self._findings()
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)
        self.assertEqual(1, counts["assessed_assets"])
        self.assertEqual(1, counts["compliant"])

    def test_duplicate_asset_id_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"].append(copy.deepcopy(inventory["assets"][0]))
        self._assert_failure("inventory.duplicate", inventory=inventory)

    def test_missing_asset_owner_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["owner_role"] = ""
        self._assert_failure("inventory.owner", inventory=inventory)

    def test_invalid_management_state_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["management_state"] = "UNBOUNDED"
        self._assert_failure("inventory.management", inventory=inventory)

    def test_privileged_asset_without_profile_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["compliance_profile"] = ""
        self._assert_failure("inventory.profile", inventory=inventory)

    def test_stale_assessment_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["collection_time"] = "2026-07-20T00:00:00Z"
        self._assert_failure("evidence.freshness", evidence=[evidence])

    def test_unsupported_os_state_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["patch_state"]["classification"] = "UNSUPPORTED_OS"
        self._assert_failure("evidence.patch", evidence=[evidence])

    def test_unknown_asset_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["asset_id"] = "ZTD-ASSET-UNKNOWN-FIXTURE"
        self._assert_failure("evidence.unknown-asset", evidence=[evidence])

    def test_automatic_patch_claim_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["patch_state"]["automatic_patching_performed"] = True
        self._assert_failure("evidence.mutation", evidence=[evidence])

    def test_endpoint_agent_install_claim_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["endpoint_agent"]["installed_by_package"] = True
        self._assert_failure("evidence.agent", evidence=[evidence])

    def test_full_mac_address_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        mac_fixture = ":".join(("aa", "bb", "cc", "dd", "ee", "ff"))
        inventory["assets"][0]["limitations"].append(f"fixture {mac_fixture}")
        self._assert_failure("privacy.mac", inventory=inventory)

    def test_secret_pattern_is_rejected(self) -> None:
        inventory = copy.deepcopy(self.inventory)
        inventory["assets"][0]["limitations"].append("client_secret=fixture")
        self._assert_failure("security.secret", inventory=inventory)

    def test_security_updates_classify_partial_without_mutation(self) -> None:
        raw = dict(self.raw, security_updates_available=2)
        evidence = COLLECTOR.normalize_record(raw)
        findings, counts = self._findings(evidence=[evidence])
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)
        self.assertEqual(1, counts["partially_compliant"])
        self.assertTrue(any(item.check == "evidence.patch" and item.level == "WARN" for item in findings))


if __name__ == "__main__":
    unittest.main()
