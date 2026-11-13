"""Regression tests for bounded Phase 2 entry and ZT-VIS-002 partial runtime."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_phase2_entry as entry  # noqa: E402


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Phase2EntryTests(unittest.TestCase):
    def copied_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        package = json.loads((ROOT / entry.PACKAGE).read_text(encoding="utf-8"))
        paths = list(entry.REQUIRED_PATHS)
        paths.extend(Path(item) for item in package["source_authorities"])
        for relative in dict.fromkeys(paths):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return temporary, root

    def test_bounded_partial_runtime_promotion_is_valid(self) -> None:
        self.assertEqual([], entry.validate(ROOT))

    def test_runtime_promotion_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.PACKAGE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["runtime_validation_status"] = "VALIDATED"
            write(path, value)
            self.assertTrue(entry.validate(root))
        finally:
            temporary.cleanup()

    def test_portal_deployment_authorization_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.PORTAL_CATALOG
            value = json.loads(path.read_text(encoding="utf-8"))
            value["deployment_authorized"] = True
            write(path, value)
            self.assertTrue(any("deployment" in item.lower() or "portal catalog" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_protected_runtime_cannot_become_authority(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.PACKAGE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["source_authorities"].append(".runtime/zero-trust/zt-vis-002/raw.txt")
            write(path, value)
            self.assertTrue(any("protected local state" in item for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_second_in_progress_action_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.EXECUTION
            value = json.loads(path.read_text(encoding="utf-8"))
            next(item for item in value["actions"] if item["action_id"] == "P2-ID-001")["current_status"] = "IN_PROGRESS"
            write(path, value)
            self.assertTrue(any("only in-progress" in item for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_contract_cannot_revoke_recorded_deployment_authorization(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.DEPLOYMENT_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["deployment_authorized"] = False
            write(path, value)
            self.assertTrue(any("contract" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_contract_cannot_allow_floating_ip(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.DEPLOYMENT_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["topology"]["floating_ip_allowed"] = True
            write(path, value)
            self.assertTrue(any("floating" in item.lower() or "topology" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_contract_requires_all_acceptance_case_classes(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.DEPLOYMENT_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["acceptance_cases"] = value["acceptance_cases"][:-1]
            write(path, value)
            self.assertTrue(any("acceptance case" in item.lower() or "schema" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_authorize_runtime(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.READINESS_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["runtime_executed"] = True
            write(path, value)
            self.assertTrue(any("readiness" in item.lower() or "schema" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_must_keep_live_authorizations_open(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.READINESS_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["remaining_gates"].remove("AUTHORIZE_LIVE_VALIDATOR")
            write(path, value)
            self.assertTrue(any("readiness" in item.lower() or "schema" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_restore_pending_external_input_state(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / entry.READINESS_CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["external_input_contract"]["review_status"] = "PENDING"
            write(path, value)
            self.assertTrue(any("readiness" in item.lower() or "schema" in item.lower() for item in entry.validate(root)))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
