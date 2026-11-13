"""Regression tests for the bounded ZT-SYS-001 package."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
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


INVENTORY = module("zt_sys_inventory", "tools/system/validate_system_inventory.py")
DRIFT = module("zt_sys_drift", "tools/system/check_configuration_drift.py")
SERVICE = module("zt_sys_service", "tools/system/validate_service_state.py")


class ZtSys001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = INVENTORY.load(ROOT / "docs/zero-trust/system-inventory.yaml")
        self.baselines = INVENTORY.load(ROOT / "docs/zero-trust/system-baseline-policy.yaml")
        self.authority = INVENTORY.load(ROOT / "docs/zero-trust/system-configuration-authority.yaml")
        self.credentials = INVENTORY.load(ROOT / "docs/zero-trust/system-credential-reference-inventory.yaml")
        self.exposures = INVENTORY.load(ROOT / "docs/zero-trust/system-service-exposure.yaml")
        self.recovery = INVENTORY.load(ROOT / "docs/zero-trust/system-recovery-readiness.yaml")
        self.integrity = INVENTORY.load(ROOT / "docs/zero-trust/system-integrity-policy.yaml")
        self.integrity_evidence = INVENTORY.load(ROOT / "docs/evidence/zero-trust/zt-sys-001-integrity-validation.yaml")
        self.service_policy = INVENTORY.load(ROOT / "docs/zero-trust/system-service-policy.yaml")
        self.service_evidence = INVENTORY.load(ROOT / "docs/evidence/zero-trust/zt-sys-001-service-state.yaml")

    def inventory_findings(self, **changes):
        values = {
            "inventory": self.inventory,
            "baselines": self.baselines,
            "authority": self.authority,
            "credentials": self.credentials,
            "exposures": self.exposures,
            "recovery": self.recovery,
        }
        values.update(changes)
        return INVENTORY.validate(**values)

    def assert_inventory_failure(self, check: str, **changes) -> None:
        findings = self.inventory_findings(**changes)
        self.assertTrue(any(item.level == "FAIL" and item.check == check for item in findings), findings)

    def test_current_inventory_is_consistent(self) -> None:
        self.assertFalse(any(item.level == "FAIL" for item in self.inventory_findings()))

    def test_duplicate_system_fails(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["systems"].append(copy.deepcopy(value["systems"][0]))
        self.assert_inventory_failure("inventory.duplicate", inventory=value)

    def test_active_system_missing_owner_fails(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["systems"][1]["owner"] = ""
        self.assert_inventory_failure("ownership.missing", inventory=value)

    def test_missing_baseline_reference_fails(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["systems"][0]["baseline_profile"] = "ZTSYS-PROFILE-MISSING"
        self.assert_inventory_failure("baseline.reference", inventory=value)

    def test_missing_privileged_access_model_fails(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["systems"][0]["privileged_access_model"] = ""
        self.assert_inventory_failure("privileged.model", inventory=value)

    def test_unknown_configuration_system_fails(self) -> None:
        value = copy.deepcopy(self.authority)
        value["configurations"][0]["system_id"] = "ZTSYS-UNKNOWN"
        self.assert_inventory_failure("authority.system", authority=value)

    def test_sensitive_configuration_hash_fails(self) -> None:
        value = copy.deepcopy(self.authority)
        value["configurations"][-1]["approved_sha256"] = "0" * 64
        self.assert_inventory_failure("authority.secret-hash", authority=value)

    def test_restore_validated_without_evidence_fails(self) -> None:
        value = copy.deepcopy(self.recovery)
        value["systems"][0]["readiness"] = "RESTORE_VALIDATED"
        value["systems"][0]["last_recovery_evidence"] = None
        self.assert_inventory_failure("recovery.evidence", recovery=value)

    def test_current_safe_configuration_checksums_match(self) -> None:
        findings = DRIFT.validate(self.authority, self.integrity, self.integrity_evidence, ROOT)
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)

    def test_checksum_drift_fails(self) -> None:
        value = copy.deepcopy(self.authority)
        value["configurations"][0]["approved_sha256"] = "0" * 64
        findings = DRIFT.validate(value, self.integrity, self.integrity_evidence, ROOT)
        self.assertTrue(any(item.level == "FAIL" and item.check == "drift.checksum" for item in findings), findings)

    def test_matched_without_evidence_fails(self) -> None:
        value = copy.deepcopy(self.integrity_evidence)
        value["records"] = value["records"][1:]
        findings = DRIFT.validate(self.authority, self.integrity, value, ROOT)
        self.assertTrue(any(item.level == "FAIL" and item.check == "drift.evidence" for item in findings), findings)

    def test_missing_authoritative_source_fails(self) -> None:
        value = copy.deepcopy(self.authority)
        value["configurations"][0]["authoritative_source"] = "missing/system-config.yaml"
        findings = DRIFT.validate(value, self.integrity, self.integrity_evidence, ROOT)
        self.assertTrue(any(item.level == "FAIL" and item.check == "source.missing" for item in findings), findings)

    def test_current_service_state_has_no_failure(self) -> None:
        findings = SERVICE.validate(self.service_policy, self.service_evidence)
        self.assertFalse(any(item.level == "FAIL" for item in findings), findings)
        self.assertTrue(any(item.level == "WARN" and item.check == "service.degraded" for item in findings), findings)

    def test_required_stopped_service_fails(self) -> None:
        value = copy.deepcopy(self.service_evidence)
        value["services"][1]["current_state"] = "STOPPED"
        findings = SERVICE.validate(self.service_policy, value)
        self.assertTrue(any(item.level == "FAIL" and item.check == "service.state" for item in findings), findings)

    def test_optional_service_does_not_false_fail_when_available(self) -> None:
        findings = SERVICE.validate(self.service_policy, self.service_evidence)
        self.assertFalse(any(item.level == "FAIL" and "RESTRICTED-VALIDATORS" in item.message for item in findings), findings)

    def test_restart_evidence_fails(self) -> None:
        value = copy.deepcopy(self.service_evidence)
        value["restart_performed"] = True
        findings = SERVICE.validate(self.service_policy, value)
        self.assertTrue(any(item.level == "FAIL" and item.check == "service.restart" for item in findings), findings)

    def test_live_wrapper_has_no_mutating_service_command(self) -> None:
        text = (ROOT / "tools/live-validation/validate-systems-live.ps1").read_text(encoding="utf-8").lower()
        forbidden = ("restart-service", "stop-service", "start-service", "systemctl restart", "docker compose up", "apt install")
        self.assertFalse(any(token in text for token in forbidden), text)

    def test_live_wrapper_has_no_broad_sudo_or_unrestricted_ssh(self) -> None:
        text = (ROOT / "tools/live-validation/validate-systems-live.ps1").read_text(encoding="utf-8").lower()
        self.assertNotIn("sudo -n bash", text)
        self.assertNotIn("ssh root@", text)
        self.assertIn("current_degraded_46_0_4", text)


if __name__ == "__main__":
    unittest.main()
