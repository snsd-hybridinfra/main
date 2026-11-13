from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_advanced_target_architecture as validator  # noqa: E402


class AdvancedTargetArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = validator.load(ROOT / "docs/zero-trust/capability-catalog.yaml")
        cls.selection = validator.load(ROOT / validator.SELECTION_PATH)
        cls.scope = validator.load(ROOT / validator.SCOPE_PATH)
        cls.dependency = validator.load(ROOT / validator.DEPENDENCY_PATH)
        cls.package = validator.load(ROOT / "docs/zero-trust/packages/zt-arc-001-package.yaml")
        cls.profile = validator.load(ROOT / "profiles/templates/openstack-vm/profile.yaml")
        cls.runbook = (ROOT / "docs/runbooks/08-preflight-validation.md").read_text(encoding="utf-8")

    def assert_failure(self, result: validator.ValidationResult, prefix: str) -> None:
        self.assertTrue(
            any(item.level == "FAIL" and item.category.startswith(prefix) for item in result.findings),
            [item.__dict__ for item in result.findings],
        )

    def validate_selection(self, selection: dict) -> validator.ValidationResult:
        result = validator.ValidationResult()
        validator.validate_selection_data(selection, self.catalog, result)
        return result

    def test_valid_repository_architecture(self) -> None:
        result = validator.run_validation(ROOT)
        self.assertFalse(any(item.level == "FAIL" for item in result.findings), [item.__dict__ for item in result.findings])

    def test_missing_capability(self) -> None:
        value = copy.deepcopy(self.selection)
        value["capabilities"].pop()
        self.assert_failure(self.validate_selection(value), "selection.coverage")

    def test_duplicate_capability(self) -> None:
        value = copy.deepcopy(self.selection)
        value["capabilities"][1]["id"] = value["capabilities"][0]["id"]
        self.assert_failure(self.validate_selection(value), "selection.coverage")

    def test_invalid_maturity_value(self) -> None:
        value = copy.deepcopy(self.selection)
        value["capabilities"][0]["target_maturity"] = "EXPERIMENTAL"
        self.assert_failure(self.validate_selection(value), "selection.maturity")

    def test_advanced_selection_without_rationale(self) -> None:
        value = copy.deepcopy(self.selection)
        item = next(row for row in value["capabilities"] if row["selection"] == "ADVANCED_PRIMARY_TARGET")
        item["rationale"] = ""
        self.assert_failure(self.validate_selection(value), "selection.advanced")

    def test_advanced_selection_without_runtime_evidence(self) -> None:
        value = copy.deepcopy(self.selection)
        item = next(row for row in value["capabilities"] if row["selection"] == "ADVANCED_PRIMARY_TARGET")
        item["evidence_requirements"] = ["configuration only"]
        self.assert_failure(self.validate_selection(value), "selection.advanced")

    def test_optimal_marked_implemented(self) -> None:
        value = copy.deepcopy(self.selection)
        item = next(row for row in value["capabilities"] if row["selection"] == "OPTIMAL_ROADMAP_ONLY")
        item["roadmap_status"] = "IMPLEMENTED"
        self.assert_failure(self.validate_selection(value), "selection.optimal")

    def test_optimal_ready_treated_as_official_maturity(self) -> None:
        value = copy.deepcopy(self.selection)
        value["capabilities"][0]["target_maturity"] = "OPTIMAL_READY"
        self.assert_failure(self.validate_selection(value), "selection.maturity")

    def test_repository_wide_advanced_score(self) -> None:
        value = copy.deepcopy(self.scope)
        value["repository_maturity"] = "ADVANCED"
        result = validator.ValidationResult()
        validator.validate_scope_data(value, result)
        self.assert_failure(result, "scope.maturity")

    def test_iac_and_cac_scope_conflict(self) -> None:
        value = copy.deepcopy(self.scope)
        value["responsibilities"]["cac"].append(value["responsibilities"]["iac"][0])
        result = validator.ValidationResult()
        validator.validate_scope_data(value, result)
        self.assert_failure(result, "scope.responsibility")

    def test_pac_without_deny_behavior(self) -> None:
        result = validator.ValidationResult()
        validator.validate_policy_contract("Policy evaluator allows changes.", result)
        self.assert_failure(result, "policy.deny")

    def test_physical_server_incorrectly_iac_provisioned(self) -> None:
        value = copy.deepcopy(self.scope)
        next(item for item in value["provider_adapters"] if item["id"] == "physical-server")["provisions_compute"] = True
        result = validator.ValidationResult()
        validator.validate_scope_data(value, result)
        self.assert_failure(result, "scope.adapter")

    def test_existing_vm_incorrectly_provisioned(self) -> None:
        value = copy.deepcopy(self.scope)
        next(item for item in value["provider_adapters"] if item["id"] == "existing-vm")["provisions_compute"] = True
        result = validator.ValidationResult()
        validator.validate_scope_data(value, result)
        self.assert_failure(result, "scope.adapter")

    def test_runbook_without_rollback(self) -> None:
        value = self.runbook.replace("## Rollback", "## Removed rollback")
        result = validator.ValidationResult()
        validator.validate_runbook_text(value, result)
        self.assert_failure(result, "runbook.rollback")

    def test_runbook_without_status(self) -> None:
        value = self.runbook.replace("## Current implementation status", "## Removed status")
        result = validator.ValidationResult()
        validator.validate_runbook_text(value, result)
        self.assert_failure(result, "runbook.status")

    def test_profile_containing_secret(self) -> None:
        value = copy.deepcopy(self.profile)
        value["access"]["password"] = "placeholder-value"
        result = validator.ValidationResult()
        validator.validate_profile_data(value, result)
        self.assert_failure(result, "profile.secret")

    def test_profile_containing_private_key_path(self) -> None:
        value = copy.deepcopy(self.profile)
        value["access"]["ssh_key_path"] = "/tmp/id_rsa"
        result = validator.ValidationResult()
        validator.validate_profile_data(value, result)
        self.assert_failure(result, "profile.private-key")

    def test_roadmap_package_marked_completed(self) -> None:
        value = copy.deepcopy(self.dependency)
        first = next(iter(value["package_status"]))
        value["package_status"][first]["implementation_status"] = "COMPLETED"
        result = validator.ValidationResult()
        validator.validate_dependency_data(value, result)
        self.assert_failure(result, "roadmap.package-status")

    def test_identity_package_cannot_claim_full_production_validation(self) -> None:
        value = copy.deepcopy(self.dependency)
        value["package_status"]["ZT-ID-001"]["runtime_scope"] = "FULL_PRODUCTION"
        result = validator.ValidationResult()
        validator.validate_dependency_data(value, result)
        self.assert_failure(result, "roadmap.package-status")

    def test_architecture_package_cannot_drop_authority_boundary(self) -> None:
        value = copy.deepcopy(self.package)
        value["runtime_validation_status"] = "RUNTIME_VALIDATED"
        value["advanced_claim"] = True
        result = validator.ValidationResult()
        validator.validate_package_data(value, result)
        self.assert_failure(result, "package.metadata")

    def test_tracked_runtime_file(self) -> None:
        result = validator.ValidationResult()
        validator.validate_tracked_runtime_paths([".runtime/zero-trust/result.txt"], result)
        self.assert_failure(result, "runtime.tracking")

    def test_unsupported_aws_or_azure_implementation_claim(self) -> None:
        value = copy.deepcopy(self.scope)
        aws = next(item for item in value["provider_adapters"] if item["id"] == "aws")
        aws["status"] = "CURRENT"
        aws["provisions_compute"] = True
        result = validator.ValidationResult()
        validator.validate_scope_data(value, result)
        self.assert_failure(result, "scope.adapter")


if __name__ == "__main__":
    unittest.main()
