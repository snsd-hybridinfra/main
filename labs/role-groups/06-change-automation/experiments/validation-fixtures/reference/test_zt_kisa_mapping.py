"""Focused positive, negative, safety and mutation tests for ZT-GOV-MAP-001."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_zero_trust as core  # noqa: E402
import zt_project_plan_common as plan  # noqa: E402

MAP = plan.AUTHORITIES["kisa_mapping"][0]
SCHEMA = plan.AUTHORITIES["kisa_mapping"][1]
SOURCE = Path("docs/references/kisa-2026-critical-infrastructure-guide.yaml")
CATALOG = Path("docs/zero-trust/capability-catalog.yaml")
MARKDOWN = Path("docs/zero-trust/mappings/zt-kisa-technical-control-map.md")
PATHS = [MAP, SCHEMA, SOURCE, CATALOG, MARKDOWN]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@contextmanager
def copied_root():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in PATHS:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        yield root


def failures(result: plan.Result, prefix: str) -> list[plan.Finding]:
    return [item for item in result.findings if item.level == "FAIL" and item.category.startswith(prefix)]


def validate(root: Path) -> plan.Result:
    result = plan.Result()
    plan.validate_kisa_mapping(root, result)
    return result


def schema_errors(data: object) -> list[str]:
    return core.validate_schema_instance(data, plan.load(ROOT / SCHEMA))


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in PATHS:
        digest.update(relative.as_posix().encode())
        digest.update((root / relative).read_bytes())
    return digest.hexdigest()


class KisaMappingFrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = plan.load(ROOT / MAP)
        cls.source = plan.load(ROOT / SOURCE)

    def test_valid_framework(self) -> None:
        with copied_root() as root:
            self.assertEqual([], failures(validate(root), "kisa."))

    def test_valid_source_metadata(self) -> None:
        self.assertEqual("2026", self.source["edition"])
        self.assertEqual(873, self.source["page_count"])
        self.assertEqual(plan.KISA_SHA256, self.source["sha256"])
        self.assertEqual(plan.KISA_DOMAINS, {item["id"]: (item["section_name"], item["code_family"], item["page_start"], item["page_end"]) for item in self.source["asset_domains"]})

    def _source_failure(self, field: str, value: object) -> plan.Result:
        with copied_root() as root:
            data = plan.load(root / SOURCE)
            if value is ...:
                data.pop(field)
            else:
                data[field] = value
            write_json(root / SOURCE, data)
            return validate(root)

    def test_invalid_guide_year(self) -> None:
        self.assertTrue(failures(self._source_failure("publication_year", 2025), "kisa.source"))

    def test_missing_source_hash(self) -> None:
        self.assertTrue(failures(self._source_failure("sha256", ...), "kisa.source"))

    def test_missing_page_count(self) -> None:
        self.assertTrue(failures(self._source_failure("page_count", ...), "kisa.source"))

    def test_valid_package_flow(self) -> None:
        self.assertEqual(plan.PACKAGE_SEQUENCE[:-1], self.mapping["package_flow"]["sequence"])
        self.assertEqual("P1-ACC-001", self.mapping["package_flow"]["terminal"])

    def test_invalid_package_order(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["package_flow"]["sequence"][0:2] = reversed(data["package_flow"]["sequence"][0:2])
        self.assertTrue(schema_errors(data))

    def test_unknown_package(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["mappings"][0]["zt_package_id"] = "ZT-UNKNOWN-001"
        self.assertTrue(schema_errors(data))

    def test_unknown_capability(self) -> None:
        with copied_root() as root:
            data = plan.load(root / MAP)
            data["mappings"][0]["zt_capability_ids"] = ["ZT-1.9.9"]
            write_json(root / MAP, data)
            self.assertTrue(failures(validate(root), "kisa.capability"))

    def test_valid_mapping_types(self) -> None:
        types = {item["mapping_type"] for item in self.mapping["mappings"]}
        self.assertTrue({"DIRECT", "SUPPORTING", "FUTURE_SCOPE", "GOVERNANCE_ONLY"}.issubset(types))

    def test_invalid_mapping_type(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["mappings"][0]["mapping_type"] = "CERTIFIED"
        self.assertTrue(schema_errors(data))

    def test_invalid_applicability(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["mappings"][0]["applicability"] = "COMPLIANT"
        self.assertTrue(schema_errors(data))

    def test_duplicate_mapping_id(self) -> None:
        with copied_root() as root:
            data = plan.load(root / MAP)
            data["mappings"][1]["mapping_id"] = data["mappings"][0]["mapping_id"]
            write_json(root / MAP, data)
            self.assertTrue(failures(validate(root), "kisa.ids"))

    def test_fabricated_kisa_item_code(self) -> None:
        with copied_root() as root:
            data = plan.load(root / MAP)
            record = next(item for item in data["mappings"] if item["kisa_item_code"] is not None)
            record["kisa_item_code"] = "U-99"
            record["mapping_id"] = record["mapping_id"].replace("U-05", "U-99")
            write_json(root / MAP, data)
            self.assertTrue(failures(validate(root), "kisa.guessed"))

    def test_required_mapping_fields(self) -> None:
        for field in ("kisa_item_name", "source_reference", "operational_impact", "version_constraints"):
            data = copy.deepcopy(self.mapping)
            data["mappings"][0].pop(field)
            self.assertTrue(schema_errors(data), field)

    def test_unsupported_status_claims(self) -> None:
        cases = {
            "implementation_status": "IMPLEMENTED",
            "runtime_validation_status": "VALIDATED",
            "maturity_status": "L3_ADVANCED",
            "compliance_status": "COMPLIANT",
        }
        for field, value in cases.items():
            data = copy.deepcopy(self.mapping)
            data["mappings"][0][field] = value
            self.assertTrue(schema_errors(data), field)

    def test_valid_exception(self) -> None:
        self.assertEqual([], schema_errors(self.mapping))
        self.assertEqual("NOT_REQUESTED", self.mapping["exception_policy"]["exception_status"])

    def test_exception_without_rationale(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["exception_policy"]["exception_reason"] = ""
        self.assertTrue(schema_errors(data))

    def test_compensating_control_without_evidence(self) -> None:
        data = copy.deepcopy(self.mapping)
        data["exception_policy"]["evidence_requirements"] = []
        self.assertTrue(schema_errors(data))

    def test_s051_rejected(self) -> None:
        with copied_root() as root:
            data = plan.load(root / MAP)
            data["metadata"]["limitations"].append("Prohibited " + "S" + "051" + " marker")
            write_json(root / MAP, data)
            self.assertTrue(failures(validate(root), "kisa.scenario"))

    def test_tracked_runtime_rejected(self) -> None:
        with copied_root() as root:
            runtime = root / ".runtime/zero-trust/zt-gov-map-001/result.txt"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("synthetic\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", runtime.relative_to(root).as_posix()], cwd=root, check=True)
            self.assertTrue(failures(validate(root), "kisa.runtime"))

    def test_markdown_yaml_synchronization(self) -> None:
        with copied_root() as root:
            path = root / MARKDOWN
            path.write_text(path.read_text(encoding="utf-8").replace("ZT-DEV-001", "ZT-DEVICE-PENDING"), encoding="utf-8")
            self.assertTrue(failures(validate(root), "kisa.sync"))

    def test_validator_is_read_only(self) -> None:
        with copied_root() as root:
            before = fingerprint(root)
            result = validate(root)
            after = fingerprint(root)
            self.assertEqual(0, result.failed, [vars(item) for item in result.findings])
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
