from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_zero_trust as validator  # noqa: E402


class ZeroTrustValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = validator.load_json_yaml(ROOT / validator.CATALOG_PATH)
        cls.baseline = validator.load_json_yaml(ROOT / validator.BASELINE_PATH)
        cls.backlog = validator.load_json_yaml(ROOT / validator.BACKLOG_PATH)
        cls.catalog_schema = validator.load_schema(ROOT / validator.CATALOG_SCHEMA_PATH)
        cls.baseline_schema = validator.load_schema(ROOT / validator.BASELINE_SCHEMA_PATH)
        cls.backlog_schema = validator.load_schema(ROOT / validator.BACKLOG_SCHEMA_PATH)

    def assert_has_failure(self, result: validator.ValidationResult, category_prefix: str) -> None:
        self.assertTrue(
            any(item.level == "FAIL" and item.category.startswith(category_prefix) for item in result.findings),
            [item.__dict__ for item in result.findings],
        )

    def test_valid_52_capability_catalog(self) -> None:
        result = validator.ValidationResult()
        validator.validate_catalog(copy.deepcopy(self.catalog), self.catalog_schema, result)
        self.assertFalse(any(item.level == "FAIL" for item in result.findings))

    def test_missing_capability_fails(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["capabilities"].pop()
        result = validator.ValidationResult()
        validator.validate_catalog(catalog, self.catalog_schema, result)
        self.assert_has_failure(result, "schema.catalog")

    def test_duplicate_capability_id_fails(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["capabilities"][1]["id"] = catalog["capabilities"][0]["id"]
        result = validator.ValidationResult()
        validator.validate_catalog(catalog, self.catalog_schema, result)
        self.assert_has_failure(result, "taxonomy.ids")

    def test_invalid_capability_id_fails(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["capabilities"][0]["id"] = "ZT-0.1.1"
        result = validator.ValidationResult()
        validator.validate_catalog(catalog, self.catalog_schema, result)
        self.assert_has_failure(result, "schema.catalog")

    def test_invalid_maturity_value_fails_schema(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["capabilities"][0]["current_maturity"] = "EXPERIMENTAL"
        errors = validator.validate_schema_instance(baseline, self.baseline_schema)
        self.assertTrue(any("invalid enum" in error for error in errors))

    def test_validated_with_design_evidence_fails(self) -> None:
        item = copy.deepcopy(self.baseline["capabilities"][0])
        item["validation_status"] = "VALIDATED"
        item["evidence_level"] = "DESIGN"
        result = validator.ValidationResult()
        validator.validate_maturity([item], result, "test")
        self.assert_has_failure(result, "maturity.test")

    def test_optimal_without_continuous_evidence_fails(self) -> None:
        item = copy.deepcopy(self.baseline["capabilities"][0])
        item["current_maturity"] = "OPTIMAL"
        item["target_maturity"] = "OPTIMAL"
        item["evidence_level"] = "RUNTIME"
        result = validator.ValidationResult()
        validator.validate_maturity([item], result, "test")
        self.assert_has_failure(result, "maturity.test")

    def test_broken_evidence_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid, reason = validator._safe_relative_reference(Path(directory), "evidence/missing/result.txt")
            self.assertFalse(valid)
            self.assertEqual(reason, "missing target")

    def test_forbidden_affirmative_overclaim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs/zero-trust").mkdir(parents=True)
            (root / "docs").mkdir(exist_ok=True)
            (root / "README.md").write_text("This platform is fully compliant.\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            result = validator.ValidationResult()
            validator.validate_overclaims(root, result)
            self.assert_has_failure(result, "claims")

    def test_malformed_yaml_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.yaml"
            path.write_text('{"capabilities": [}', encoding="utf-8")
            with self.assertRaises(ValueError):
                validator.load_json_yaml(path)

    def test_duplicate_json_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.yaml"
            path.write_text('{"id": "ZT-7.1", "id": "ZT-7.2"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                validator.load_json_yaml(path)

    def test_inconsistent_baseline_summary_count_fails(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["summary"]["validated"] += 1
        result = validator.ValidationResult()
        validator.validate_baseline(baseline, self.baseline_schema, result)
        self.assert_has_failure(result, "baseline.summary")

    def test_cross_cutting_capability_id_validation(self) -> None:
        self.assertRegex("ZT-7.1", validator.CAPABILITY_ID_RE)
        self.assertRegex("ZT-8.6", validator.CAPABILITY_ID_RE)
        self.assertIsNone(validator.CAPABILITY_ID_RE.fullmatch("ZT-7.1.1"))
        self.assertIsNone(validator.CAPABILITY_ID_RE.fullmatch("ZT-8.0"))

    def test_invalid_backlog_applicability_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        backlog["capabilities"][0]["applicability"] = "SOMETIMES"
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "schema.backlog")

    def test_missing_backlog_capability_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        backlog["capabilities"].pop()
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "schema.backlog")

    def test_invalid_backlog_dependency_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        backlog["capabilities"][0]["dependency_ids"] = ["ZT-9.1"]
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assertTrue(any(item.level == "FAIL" for item in result.findings))

    def test_backlog_dependency_cycle_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        first = next(item for item in backlog["capabilities"] if item["id"] == "ZT-1.1.1")
        first["dependency_ids"] = ["ZT-1.1.2"]
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "backlog.dependencies")

    def test_invalid_backlog_wave_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        backlog["capabilities"][0]["target_wave"] = "W9"
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "schema.backlog")

    def test_backlog_wave_cannot_precede_dependency(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        item = next(record for record in backlog["capabilities"] if record["id"] == "ZT-1.1.2")
        item["target_wave"] = "W0"
        for wave in backlog["waves"]:
            if item["id"] in wave["capabilities"]:
                wave["capabilities"].remove(item["id"])
        next(wave for wave in backlog["waves"] if wave["id"] == "W0")["capabilities"].append(item["id"])
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "backlog.waves")

    def test_unsupported_validated_backlog_status_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        item = next(record for record in backlog["capabilities"] if record["evidence_level"] == "NONE")
        item["validation_status"] = "VALIDATED"
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "backlog.status")

    def test_empty_package_test_boundary_fails(self) -> None:
        backlog = copy.deepcopy(self.backlog)
        backlog["capabilities"][0]["future_package_test_boundary"] = ""
        result = validator.ValidationResult()
        validator.validate_backlog(backlog, self.backlog_schema, self.catalog, result)
        self.assert_has_failure(result, "schema.backlog")

    def _foundation_package(self) -> dict:
        return {
            "package_id": "ZT-FND-001",
            "implementation_status": "IMPLEMENTED_CONFIGURATION_ONLY",
            "validation_status": "GAP_IDENTIFIED",
            "current_maturity": "UNASSESSED",
            "target_maturity": "INITIAL",
            "evidence_authority": "MISSING",
            "capability_mappings": ["ZT-4.1.1", "ZT-7.1"],
        }

    def _catalog_ids(self) -> set[str]:
        return {item["id"] for item in self.catalog["capabilities"]}

    def test_foundation_invalid_evidence_authority_fails(self) -> None:
        package = self._foundation_package()
        package["evidence_authority"] = "ASSUMED_RUNTIME"
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_foundation_unignored_runtime_fails(self) -> None:
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(self._foundation_package(), self._catalog_ids(), None, False, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_foundation_live_authority_without_record_fails(self) -> None:
        package = self._foundation_package()
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_foundation_codex_record_without_commands_fails(self) -> None:
        package = self._foundation_package()
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        execution = {"execution_authority": "CODEX_EXECUTED_LIVE_RUNTIME", "commands": []}
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(package, self._catalog_ids(), execution, True, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_foundation_validated_with_failed_target_fails(self) -> None:
        package = self._foundation_package()
        package["validation_status"] = "VALIDATED"
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        execution = {
            "execution_authority": "CODEX_EXECUTED_LIVE_RUNTIME",
            "commands": ["validate-all", "validate-host"],
            "results": {
                "openstack": {"exit_code": 0, "fail": 0},
                "eve": {"exit_code": 1, "fail": 1},
            },
            "security_boundary": {
                "interactive_shell_blocked": True,
                "arbitrary_command_blocked": True,
                "credential_read_blocked": True,
            },
        }
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(package, self._catalog_ids(), execution, True, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_foundation_optimal_target_fails(self) -> None:
        package = self._foundation_package()
        package["target_maturity"] = "OPTIMAL"
        result = validator.ValidationResult()
        validator.validate_foundation_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-fnd-001")

    def test_missing_foundation_package_document_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / validator.FOUNDATION_PACKAGE_PATH.parent).mkdir(parents=True)
            (root / ".gitignore").write_text(".runtime/zero-trust/\n", encoding="utf-8")
            result = validator.ValidationResult()
            validator.validate_foundation_package(root, self.catalog, result)
            self.assert_has_failure(result, "package.zt-fnd-001.files")

    def _router_package(self) -> dict:
        return {
            "package_id": "ZT-NET-001",
            "implementation_status": "IMPLEMENTED",
            "validation_status": "GAP_IDENTIFIED",
            "current_maturity": "UNASSESSED",
            "target_maturity": "INITIAL",
            "evidence_authority": "MISSING",
            "capability_mappings": ["ZT-3.1.1", "ZT-7.1"],
        }

    def test_router_invalid_capability_id_fails(self) -> None:
        package = self._router_package()
        package["capability_mappings"] = ["ZT-99.99.99"]
        result = validator.ValidationResult()
        validator.validate_router_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-net-001")

    def test_router_live_authority_without_record_fails(self) -> None:
        package = self._router_package()
        package["validation_status"] = "PARTIALLY_VALIDATED"
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        result = validator.ValidationResult()
        validator.validate_router_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-net-001")

    def test_router_validated_with_failed_checks_fails(self) -> None:
        package = self._router_package()
        package["validation_status"] = "VALIDATED"
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        execution = {
            "execution_authority": "CODEX_EXECUTED_LIVE_RUNTIME",
            "commands": ["validate-routing"],
            "results": {"exit_code": 1, "fail": 1},
            "validation": {"access_control": "FAIL"},
            "security_boundary": {
                "interactive_shell_blocked": True,
                "arbitrary_command_blocked": True,
                "configuration_command_blocked": True,
                "arbitrary_ping_blocked": True,
            },
        }
        result = validator.ValidationResult()
        validator.validate_router_package_data(package, self._catalog_ids(), execution, True, result)
        self.assert_has_failure(result, "package.zt-net-001")

    def test_router_runtime_validated_with_failed_checks_fails(self) -> None:
        package = self._router_package()
        package["validation_status"] = "RUNTIME_VALIDATED"
        package["evidence_authority"] = "CODEX_EXECUTED_LIVE_RUNTIME"
        execution = {
            "execution_authority": "CODEX_EXECUTED_LIVE_RUNTIME",
            "commands": ["validate-routing"],
            "results": {"exit_code": 1, "fail": 1},
            "validation": {"access_control": "FAIL"},
            "security_boundary": {
                "interactive_shell_blocked": True,
                "arbitrary_command_blocked": True,
                "configuration_command_blocked": True,
                "arbitrary_ping_blocked": True,
            },
        }
        result = validator.ValidationResult()
        validator.validate_router_package_data(package, self._catalog_ids(), execution, True, result)
        self.assert_has_failure(result, "package.zt-net-001")

    def test_router_optimal_target_fails(self) -> None:
        package = self._router_package()
        package["target_maturity"] = "OPTIMAL"
        result = validator.ValidationResult()
        validator.validate_router_package_data(package, self._catalog_ids(), None, True, result)
        self.assert_has_failure(result, "package.zt-net-001")

    def test_missing_router_package_document_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / validator.ROUTER_PACKAGE_PATH.parent).mkdir(parents=True)
            (root / ".gitignore").write_text(".runtime/zero-trust/\n", encoding="utf-8")
            result = validator.ValidationResult()
            validator.validate_router_package(root, self.catalog, result)
            self.assert_has_failure(result, "package.zt-net-001.files")

    def test_repository_private_key_pattern_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs/private-key.txt").write_text(
                "-----BEGIN OPENSSH " + "PRIVATE KEY-----\nnot-a-real-key\n",
                encoding="utf-8",
            )
            result = validator.ValidationResult()
            validator.validate_sensitive_data(root, result)
            self.assert_has_failure(result, "sensitive-data")


if __name__ == "__main__":
    unittest.main()
