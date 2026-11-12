"""Regression tests for ZT-APP-001."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


INVENTORY = module("zt_app_inventory", "tools/application/validate_application_inventory.py")
DEPLOYMENT = module("zt_app_deployment", "tools/application/validate_secure_deployment.py")
SCANS = module("zt_app_scans", "tools/application/run_security_scans.py")


class ZtApp001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.apps = json.loads((ROOT / "docs/zero-trust/application-inventory.yaml").read_text(encoding="utf-8"))
        self.workloads = json.loads((ROOT / "docs/zero-trust/workload-inventory.yaml").read_text(encoding="utf-8"))
        self.policy = json.loads((ROOT / "docs/zero-trust/secure-deployment-policy.yaml").read_text(encoding="utf-8"))
        self.components = json.loads((ROOT / "docs/zero-trust/software-component-inventory.yaml").read_text(encoding="utf-8"))
        self.compose = (ROOT / "observability/logging/compose.yaml").read_text(encoding="utf-8")

    def assert_inventory_failure(self, check: str, apps=None, workloads=None) -> None:
        findings = INVENTORY.validate(apps or self.apps, workloads or self.workloads)
        self.assertTrue(any(item.level == "FAIL" and item.check == check for item in findings), findings)

    def test_valid_inventory(self) -> None:
        findings = INVENTORY.validate(self.apps, self.workloads)
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)

    def test_duplicate_application(self) -> None:
        value = copy.deepcopy(self.apps); value["applications"].append(copy.deepcopy(value["applications"][0]))
        self.assert_inventory_failure("applications.duplicate", apps=value)

    def test_duplicate_workload(self) -> None:
        value = copy.deepcopy(self.workloads); value["workloads"].append(copy.deepcopy(value["workloads"][0]))
        self.assert_inventory_failure("workloads.duplicate", workloads=value)

    def test_orphan_workload(self) -> None:
        value = copy.deepcopy(self.workloads); value["workloads"][0]["application_id"] = "ZTA-APP-UNKNOWN"
        self.assert_inventory_failure("workloads.orphan", workloads=value)

    def test_missing_owner(self) -> None:
        value = copy.deepcopy(self.apps); value["applications"][0]["owner"] = ""
        self.assert_inventory_failure("applications.owner", apps=value)

    def test_unknown_criticality_warns(self) -> None:
        value = copy.deepcopy(self.apps); value["applications"][0]["criticality"] = "UNKNOWN"
        findings = INVENTORY.validate(value, self.workloads)
        self.assertTrue(any(item.level == "WARN" and item.check == "applications.criticality" for item in findings))

    def test_running_workload_requires_health(self) -> None:
        value = copy.deepcopy(self.workloads); value["workloads"][0]["health_check"] = "UNKNOWN"
        self.assert_inventory_failure("workloads.health", workloads=value)

    def test_running_workload_requires_runtime_evidence(self) -> None:
        value = copy.deepcopy(self.workloads); value["workloads"][0]["evidence_level"] = "CONFIGURATION"
        self.assert_inventory_failure("workloads.evidence", workloads=value)

    def test_secure_deployment_has_only_documented_warnings(self) -> None:
        findings = DEPLOYMENT.validate(self.policy, self.compose, self.components)
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)
        self.assertTrue(any(item.check == "pilot.root" for item in findings))

    def test_privileged_container_fails(self) -> None:
        compose = self.compose.replace("  alloy:\n", "  alloy:\n    privileged: true\n", 1)
        findings = DEPLOYMENT.validate(self.policy, compose, self.components)
        self.assertTrue(any(item.level == "FAIL" and item.check == "pilot.privilege" for item in findings))

    def test_missing_healthcheck_fails(self) -> None:
        start = self.compose.index("  alloy:"); end = self.compose.index("\n  grafana:", start)
        alloy = self.compose[start:end].replace("healthcheck:", "health_check_removed:")
        compose = self.compose[:start] + alloy + self.compose[end:]
        findings = DEPLOYMENT.validate(self.policy, compose, self.components)
        self.assertTrue(any(item.level == "FAIL" and item.check == "pilot.configuration" for item in findings))

    def test_automatic_deployment_fails(self) -> None:
        policy = copy.deepcopy(self.policy); policy["automatic_deployment"] = True
        findings = DEPLOYMENT.validate(policy, self.compose, self.components)
        self.assertTrue(any(item.level == "FAIL" and item.check == "policy.mutation" for item in findings))

    def test_missing_sbom_fails(self) -> None:
        findings = DEPLOYMENT.validate(self.policy, self.compose, None)
        self.assertTrue(any(item.level == "FAIL" and item.check == "sbom.missing" for item in findings))

    def test_complete_claim_without_complete_artifact_fails(self) -> None:
        components = copy.deepcopy(self.components); components["sbom_status"] = "COMPLETE_FOR_SCOPE"
        findings = DEPLOYMENT.validate(self.policy, self.compose, components)
        self.assertTrue(any(item.level == "FAIL" and item.check == "sbom.status" for item in findings))

    def test_built_in_scanner_detects_fixture_and_components(self) -> None:
        fixture = "gh" + "p_" + "A" * 24
        self.assertTrue(any(pattern.search(fixture) for pattern in SCANS.SECRET_PATTERNS))
        components, cdx = SCANS.compose_components(self.compose, "2026-07-22T00:00:00Z")
        self.assertEqual(3, len(components)); self.assertEqual(3, len(cdx))


if __name__ == "__main__":
    unittest.main()
