from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "validate_zt_id_001.py"
SPEC = importlib.util.spec_from_file_location("validate_zt_id_001", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load ZT-ID-001 validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class ZtId001TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = VALIDATOR.load_json_document(ROOT / VALIDATOR.CATALOG_PATH)

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        paths = [
            VALIDATOR.PACKAGE_PATH,
            VALIDATOR.EVIDENCE_PATH,
            VALIDATOR.RUNTIME_EVIDENCE_PATH,
            VALIDATOR.POSITIVE_FIXTURES,
            VALIDATOR.NEGATIVE_FIXTURES,
            *VALIDATOR.MODEL_PATHS.values(),
            *VALIDATOR.SCHEMA_PATHS.values(),
        ]
        for relative in paths:
            target = self.temp_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        self.package = self._load(VALIDATOR.PACKAGE_PATH)
        self.evidence = self._load(VALIDATOR.EVIDENCE_PATH)
        self.runtime_evidence = self._load(VALIDATOR.RUNTIME_EVIDENCE_PATH)
        self.inventory = self._load(VALIDATOR.MODEL_PATHS["inventory"])
        self.roles = self._load(VALIDATOR.MODEL_PATHS["roles"])
        self.authentication = self._load(VALIDATOR.MODEL_PATHS["authentication"])
        self.lifecycle = self._load(VALIDATOR.MODEL_PATHS["lifecycle"])
        self.positive = self._load(VALIDATOR.POSITIVE_FIXTURES)["cases"]
        self.negative = self._load(VALIDATOR.NEGATIVE_FIXTURES)["cases"]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _load(self, relative: Path) -> dict:
        return json.loads((self.temp_root / relative).read_text(encoding="utf-8"))

    def _package_codes(self, package: dict | None = None) -> set[str]:
        return VALIDATOR.validate_package_document(package or self.package, self.catalog)

    def _inventory_codes(self, inventory: dict | None = None) -> set[str]:
        return VALIDATOR.validate_identity_inventory(inventory or self.inventory, self.roles)

    def _negative_codes(self, case_id: str) -> set[str]:
        case = next(item for item in self.negative if item["case_id"] == case_id)
        return VALIDATOR.validate_negative_case(
            case,
            self.package,
            self.inventory,
            self.roles,
            self.authentication,
            self.catalog,
        )

    def _assert_negative(self, case_id: str, code: str) -> None:
        self.assertIn(code, self._negative_codes(case_id))

    def _decision(self, case_id: str) -> dict:
        case = next(item for item in self.positive if item["case_id"] == case_id)
        return VALIDATOR.evaluate_request(
            case["request"],
            self.inventory,
            self.roles,
            self.authentication,
            case_id,
        )

    # Package and schema

    def test_valid_package(self) -> None:
        self.assertEqual(set(), self._package_codes())

    def test_missing_package_id(self) -> None:
        value = copy.deepcopy(self.package)
        value.pop("package_id")
        self.assertIn("INVALID_PACKAGE_ID", self._package_codes(value))

    def test_wrong_package_phase(self) -> None:
        value = copy.deepcopy(self.package)
        value["phase"] = "PHASE_2"
        self.assertIn("INVALID_PACKAGE_PHASE", self._package_codes(value))

    def test_unsupported_implementation_claim(self) -> None:
        value = copy.deepcopy(self.package)
        value["implementation_status"] = "RUNTIME_IMPLEMENTED"
        self.assertIn("INVALID_PACKAGE_STATE", self._package_codes(value))

    def test_unsupported_runtime_claim(self) -> None:
        self._assert_negative("NEG-026", "UNSUPPORTED_RUNTIME_CLAIM")

    def test_unsupported_maturity_claim(self) -> None:
        self._assert_negative("NEG-027", "UNSUPPORTED_MATURITY_CLAIM")

    def test_missing_capability_mapping(self) -> None:
        value = copy.deepcopy(self.package)
        value["capability_ids"].pop()
        self.assertIn("MISSING_CAPABILITY_MAPPING", self._package_codes(value))

    def test_duplicate_capability_mapping(self) -> None:
        value = copy.deepcopy(self.package)
        value["capability_ids"].append(value["capability_ids"][0])
        self.assertIn("DUPLICATE_CAPABILITY_MAPPING", self._package_codes(value))

    def test_invalid_schema_version(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["schema_version"] = "version-one"
        schema_validator = VALIDATOR.LocalSchemaValidator(self.temp_root)
        errors = schema_validator.validate(value, VALIDATOR.SCHEMA_PATHS["inventory"])
        self.assertTrue(errors)

    # Identity subjects

    def test_valid_human_operator(self) -> None:
        identity = self.inventory["identities"][0]
        self.assertEqual("HUMAN_OPERATOR", identity["identity_type"])
        self.assertEqual(set(), self._inventory_codes())

    def test_valid_automation_identity(self) -> None:
        identity = self.inventory["identities"][3]
        self.assertEqual("AUTOMATION_IDENTITY", identity["identity_type"])
        self.assertFalse(identity["interactive_access"])

    def test_valid_validator_identity(self) -> None:
        identity = self.inventory["identities"][4]
        self.assertEqual("VALIDATOR_IDENTITY", identity["identity_type"])
        self.assertFalse(identity["interactive_access"])

    def test_valid_break_glass_design(self) -> None:
        identity = self.inventory["identities"][5]
        self.assertEqual("BREAK_GLASS_IDENTITY", identity["identity_type"])
        self.assertEqual("REQUIRED", identity["logging_requirement"])
        self.assertEqual(set(), self._inventory_codes())

    def test_missing_identity_id(self) -> None:
        self._assert_negative("NEG-001", "MISSING_IDENTITY_ID")

    def test_duplicate_identity_id(self) -> None:
        self._assert_negative("NEG-002", "DUPLICATE_IDENTITY_ID")

    def test_missing_accountable_owner(self) -> None:
        self._assert_negative("NEG-004", "MISSING_ACCOUNTABLE_OWNER")

    def test_unknown_identity_type(self) -> None:
        self._assert_negative("NEG-003", "UNKNOWN_IDENTITY_TYPE")

    def test_invalid_lifecycle_state(self) -> None:
        self._assert_negative("NEG-022", "INVALID_LIFECYCLE_STATE")

    def test_expired_identity(self) -> None:
        self._assert_negative("NEG-007", "IDENTITY_EXPIRED")

    def test_revoked_identity_with_active_role(self) -> None:
        self._assert_negative("NEG-008", "REVOKED_IDENTITY_HAS_ROLES")

    def test_shared_privileged_identity(self) -> None:
        self._assert_negative("NEG-005", "SHARED_PRIVILEGED_IDENTITY")

    # Role and authorization

    def test_read_only_allow(self) -> None:
        self.assertEqual("ALLOW", self._decision("POS-001")["decision"])

    def test_validation_operator_allow(self) -> None:
        self.assertEqual("ALLOW", self._decision("POS-002")["decision"])

    def test_mutating_request_with_approval(self) -> None:
        decision = self._decision("POS-007")
        self.assertEqual("ALLOW", decision["decision"])
        self.assertIn("APPROVAL_PRESENT", decision["reason_codes"])

    def test_unregistered_identity_deny(self) -> None:
        self._assert_negative("NEG-010", "UNREGISTERED_IDENTITY")

    def test_read_only_identity_mutating_request_deny(self) -> None:
        self._assert_negative("NEG-011", "ACTION_NOT_ALLOWED_FOR_ROLE")

    def test_invalid_role_deny(self) -> None:
        self._assert_negative("NEG-021", "INVALID_ROLE")

    def test_separation_of_duties_conflict(self) -> None:
        self._assert_negative("NEG-020", "SEPARATION_OF_DUTIES_CONFLICT")

    def test_approval_missing(self) -> None:
        self._assert_negative("NEG-031", "APPROVAL_REQUIRED")

    def test_default_deny(self) -> None:
        self.assertEqual(
            "DENY_BY_DEFAULT_FOR_UNREGISTERED_IDENTITY",
            self.roles["default_policy"],
        )

    # Authentication assurance

    def test_privileged_human_requiring_mfa(self) -> None:
        identity = self.inventory["identities"][1]
        self.assertEqual("REQUIRED_NOT_IMPLEMENTED", identity["mfa_requirement"])

    def test_privileged_human_without_mfa_rejected(self) -> None:
        self._assert_negative("NEG-006", "PRIVILEGED_MFA_REQUIRED")

    def test_service_identity_incorrectly_interactive(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][8]["interactive_access"] = True
        self.assertIn("SERVICE_INTERACTIVE_ACCESS", self._inventory_codes(value))

    def test_automation_identity_incorrectly_interactive(self) -> None:
        self._assert_negative("NEG-012", "AUTOMATION_INTERACTIVE_ACCESS")

    def test_fictional_mfa_enforcement_claim_rejected(self) -> None:
        self._assert_negative("NEG-024", "FICTIONAL_MFA_ENFORCEMENT")

    def test_fictional_oidc_deployment_claim_rejected(self) -> None:
        self._assert_negative("NEG-025", "FICTIONAL_OIDC_DEPLOYMENT")

    # Break glass

    def test_bounded_break_glass_decision(self) -> None:
        self.assertEqual("ALLOW", self._decision("POS-006")["decision"])

    def test_break_glass_missing_expiration(self) -> None:
        self._assert_negative("NEG-014", "BREAK_GLASS_EXPIRATION_REQUIRED")

    def test_break_glass_missing_owner(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][5].pop("accountable_owner")
        self.assertIn("MISSING_ACCOUNTABLE_OWNER", self._inventory_codes(value))

    def test_break_glass_missing_logging(self) -> None:
        self._assert_negative("NEG-015", "BREAK_GLASS_LOGGING_REQUIRED")

    def test_break_glass_missing_rollback(self) -> None:
        self._assert_negative("NEG-032", "BREAK_GLASS_ROLLBACK_REQUIRED")

    def test_break_glass_missing_recovery(self) -> None:
        self._assert_negative("NEG-016", "BREAK_GLASS_RECOVERY_REQUIRED")

    def test_break_glass_missing_approval(self) -> None:
        self._assert_negative("NEG-033", "BREAK_GLASS_APPROVAL_REQUIRED")

    def test_unrestricted_permanent_emergency_access_rejected(self) -> None:
        self._assert_negative("NEG-034", "UNRESTRICTED_BREAK_GLASS_SCOPE")

    # Secrets and privacy

    def test_valid_external_secret_reference(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][3]["secret_references"] = [
            "external-secret://synthetic-logical-name"
        ]
        self.assertEqual(set(), self._inventory_codes(value))

    def test_plaintext_password_rejected(self) -> None:
        self._assert_negative("NEG-017", "PLAINTEXT_SECRET_MATERIAL")

    def test_token_rejected(self) -> None:
        self._assert_negative("NEG-019", "TOKEN_OR_CLIENT_SECRET_MATERIAL")

    def test_private_key_rejected(self) -> None:
        self._assert_negative("NEG-018", "PRIVATE_KEY_MATERIAL")

    def test_mfa_seed_rejected(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][0]["mfa_seed"] = "SYNTHETIC_MFA_SEED_FIXTURE"
        self.assertIn("MFA_SEED_MATERIAL", self._inventory_codes(value))

    def test_recovery_code_rejected(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][0]["recovery_codes"] = ["SYNTHETIC_CODE"]
        self.assertIn("RECOVERY_CODE_MATERIAL", self._inventory_codes(value))

    def test_production_style_identity_export_rejected(self) -> None:
        self._assert_negative("NEG-030", "PRODUCTION_IDENTITY_DATA_PROHIBITED")

    def test_excessive_personal_data_rejected(self) -> None:
        value = copy.deepcopy(self.inventory)
        value["identities"][0]["personal_email"] = "synthetic-at-example.invalid"
        self.assertIn("EXCESSIVE_PERSONAL_DATA", self._inventory_codes(value))

    # Evidence

    def _evidence_codes(self, evidence: dict | None = None) -> set[str]:
        return VALIDATOR.validate_evidence_document(
            evidence or self.evidence, self.package, self.positive, self.negative
        )

    def test_valid_local_evidence(self) -> None:
        self.assertEqual(set(), self._evidence_codes())

    def _runtime_evidence_codes(self, evidence: dict | None = None) -> set[str]:
        return VALIDATOR.validate_runtime_evidence_document(
            evidence or self.runtime_evidence, self.package
        )

    def test_valid_runtime_evidence(self) -> None:
        self.assertEqual(set(), self._runtime_evidence_codes())

    def test_runtime_evidence_unexpected_allowance_rejected(self) -> None:
        value = copy.deepcopy(self.runtime_evidence)
        value["unexpected_allowances"] = 1
        self.assertIn(
            "RUNTIME_EVIDENCE_STATUS_MISMATCH",
            self._runtime_evidence_codes(value),
        )

    def test_runtime_evidence_count_mismatch_rejected(self) -> None:
        value = copy.deepcopy(self.runtime_evidence)
        value["negative_denied_count"] -= 1
        self.assertIn(
            "RUNTIME_EVIDENCE_COUNT_MISMATCH",
            self._runtime_evidence_codes(value),
        )

    def test_runtime_evidence_provider_claim_rejected(self) -> None:
        value = copy.deepcopy(self.runtime_evidence)
        value["identity_provider_deployed"] = True
        self.assertIn(
            "RUNTIME_EVIDENCE_STATUS_MISMATCH",
            self._runtime_evidence_codes(value),
        )

    def test_runtime_claim_without_runtime_execution_rejected(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["execution_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        self.assertIn("EVIDENCE_RUNTIME_CLAIM_MISMATCH", self._evidence_codes(value))

    def test_evidence_count_mismatch(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["pass_count"] += 1
        self.assertIn("EVIDENCE_COUNT_MISMATCH", self._evidence_codes(value))

    def test_missing_validator_version(self) -> None:
        value = copy.deepcopy(self.evidence)
        value.pop("validator_version")
        self.assertIn("MISSING_VALIDATOR_VERSION", self._evidence_codes(value))

    def test_missing_policy_version(self) -> None:
        value = copy.deepcopy(self.evidence)
        value.pop("policy_version")
        self.assertIn("MISSING_POLICY_VERSION", self._evidence_codes(value))

    def test_missing_limitation(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["limitations"] = []
        self.assertIn("MISSING_EVIDENCE_LIMITATION", self._evidence_codes(value))

    def test_package_evidence_status_mismatch(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["status"] = "RUNTIME_VALIDATION_ONLY"
        self.assertIn("PACKAGE_EVIDENCE_STATUS_MISMATCH", self._evidence_codes(value))

    # Repository integrity

    def test_tracked_runtime_reference_rejected(self) -> None:
        self._assert_negative("NEG-029", "TRACKED_RUNTIME_PROHIBITED")

    def test_validator_mutation_detected(self) -> None:
        before = {"fixture.txt": "aaa"}
        after = {"fixture.txt": "bbb"}
        self.assertEqual(
            ["fixture.txt"], VALIDATOR.detect_repository_mutation(before, after)
        )

    def test_valid_repository_baseline_passes(self) -> None:
        report = VALIDATOR.validate(ROOT, strict=True)
        self.assertEqual(0, report["exit_status"])
        self.assertTrue(report["runtime_executed"])
        self.assertTrue(report["live_identity_changed"])


if __name__ == "__main__":
    unittest.main()
