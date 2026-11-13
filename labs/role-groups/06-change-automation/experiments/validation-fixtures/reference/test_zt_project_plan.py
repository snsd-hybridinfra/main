"""Regression and negative tests for ZT-PROJECT-PLAN-001 authorities."""

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

import validate_scenario_retirement as retirement  # noqa: E402
import validate_zero_trust as core  # noqa: E402
import zt_project_plan_common as plan  # noqa: E402


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@contextmanager
def copied_root(paths: list[Path]):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        yield root


def failures(result: plan.Result, prefix: str) -> list[plan.Finding]:
    return [item for item in result.findings if item.level == "FAIL" and item.category.startswith(prefix)]


def repository_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts):
        if "__pycache__" in path.parts or "tmp" in path.parts:
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class ProjectPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.roadmap = plan.load(ROOT / plan.AUTHORITIES["roadmap"][0])
        self.execution = plan.load(ROOT / plan.AUTHORITIES["execution_plan"][0])
        self.maturity = plan.load(ROOT / plan.AUTHORITIES["maturity_target"][0])
        self.milestones = plan.load(ROOT / plan.AUTHORITIES["milestones"][0])
        self.acceptance = plan.load(ROOT / plan.AUTHORITIES["acceptance_cases"][0])
        self.status = plan.load(ROOT / plan.AUTHORITIES["package_status"][0])

    def test_official_project_titles(self) -> None:
        result = plan.Result()
        plan.validate_project_definition(ROOT, result)
        self.assertFalse(failures(result, "project"), [vars(item) for item in result.findings])

    def test_valid_phase_0_to_5_plan(self) -> None:
        result = plan.run("roadmap", ROOT, strict=True)
        self.assertEqual(0, result.failed, [vars(item) for item in result.findings])

    def test_phase2_entry_and_scheduler_deferred(self) -> None:
        states = {item["action_id"]: item["current_status"] for item in self.execution["actions"]}
        self.assertEqual("COMPLETED", states["P1-RV-001"])
        self.assertEqual("COMPLETED", states["P1-ACC-001"])
        self.assertEqual("IN_PROGRESS", states["P2-VIS-001"])
        self.assertEqual("NOT_STARTED", states["P1-SCH-001"])
        self.assertEqual(1, list(states.values()).count("IN_PROGRESS"))
        action = next(item for item in self.execution["actions"] if item["action_id"] == "P1-SCH-001")
        self.assertEqual("PHASE_5", action["phase"])
        self.assertEqual(["P5-DEMO-001"], action["dependencies"])

    def test_invalid_phase_order(self) -> None:
        paths = [plan.AUTHORITIES["roadmap"][0], plan.AUTHORITIES["roadmap"][1], Path("docs/zero-trust/final-roadmap.md")]
        with copied_root(paths) as root:
            data = copy.deepcopy(self.roadmap)
            data["phase_order"][1], data["phase_order"][2] = data["phase_order"][2], data["phase_order"][1]
            write_json(root / plan.AUTHORITIES["roadmap"][0], data)
            result = plan.Result()
            plan.validate_roadmap(root, result)
            self.assertTrue(failures(result, "roadmap"))

    def test_valid_critical_path(self) -> None:
        actions = {item["action_id"] for item in self.execution["actions"]}
        self.assertTrue(set(self.execution["critical_path"]).issubset(actions))

    def test_invalid_package_dependency(self) -> None:
        data = copy.deepcopy(self.execution)
        action = next(item for item in data["actions"] if item["action_id"] == "P1-RV-001")
        action["dependencies"] = ["P1-SCH-001"]
        result = plan.Result()
        plan.validate_dependency_data(data, result)
        self.assertTrue(failures(result, "dependency"))

    def test_cv_before_prerequisites_rejected(self) -> None:
        data = copy.deepcopy(self.execution)
        action = next(item for item in data["actions"] if item["action_id"] == "P1-CV-001")
        action["prerequisites"] = ["ZT-FND-001 accepted"]
        result = plan.Result()
        plan.validate_dependency_data(data, result)
        self.assertTrue(failures(result, "dependency.cv"))

    def test_sch_before_final_demo_rejected(self) -> None:
        data = copy.deepcopy(self.execution)
        action = next(item for item in data["actions"] if item["action_id"] == "P1-SCH-001")
        action["dependencies"] = ["P1-RV-001"]
        result = plan.Result()
        plan.validate_dependency_data(data, result)
        self.assertTrue(failures(result, "dependency.rule"))

    def test_l3_claim_without_evidence_rejected(self) -> None:
        paths = [plan.AUTHORITIES["maturity_target"][0], plan.AUTHORITIES["maturity_target"][1], Path("docs/zero-trust/maturity-target.md")]
        with copied_root(paths) as root:
            data = copy.deepcopy(self.maturity)
            data["l3_completion_decision"] = "L3_ADVANCED_SUPPORTED_BY_EVIDENCE"
            write_json(root / plan.AUTHORITIES["maturity_target"][0], data)
            result = plan.Result()
            plan.validate_maturity_target(root, result)
            self.assertTrue(failures(result, "maturity.claim"))

    def test_active_l4_implementation_claim_rejected(self) -> None:
        paths = [plan.AUTHORITIES["maturity_target"][0], plan.AUTHORITIES["maturity_target"][1], Path("docs/zero-trust/maturity-target.md")]
        with copied_root(paths) as root:
            data = copy.deepcopy(self.maturity)
            data["l4_roadmap"][0]["implementation_status"] = "IMPLEMENTED"
            write_json(root / plan.AUTHORITIES["maturity_target"][0], data)
            result = plan.Result()
            plan.validate_maturity_target(root, result)
            self.assertTrue(failures(result, "maturity"))

    def test_valid_l4_roadmap_only(self) -> None:
        self.assertTrue(all(item["implementation_status"] == "ROADMAP_ONLY" and item["runtime_validation_status"] == "NOT_VALIDATED" and item["maturity_claim"] == "NOT_CLAIMED" for item in self.maturity["l4_roadmap"]))

    def test_missing_evidence_requirement_rejected(self) -> None:
        data = copy.deepcopy(self.execution)
        data["actions"][0]["required_evidence"] = []
        schema = plan.load(ROOT / plan.AUTHORITIES["execution_plan"][1])
        self.assertTrue(core.validate_schema_instance(data, schema))

    def test_missing_rollback_rejected(self) -> None:
        data = copy.deepcopy(self.execution)
        data["actions"][4]["rollback_requirements"] = []
        schema = plan.load(ROOT / plan.AUTHORITIES["execution_plan"][1])
        self.assertTrue(core.validate_schema_instance(data, schema))

    def test_missing_stop_condition_rejected(self) -> None:
        data = copy.deepcopy(self.execution)
        data["actions"][4]["stop_conditions"] = []
        schema = plan.load(ROOT / plan.AUTHORITIES["execution_plan"][1])
        self.assertTrue(core.validate_schema_instance(data, schema))

    def test_completed_milestone_cannot_return_to_pending(self) -> None:
        data = copy.deepcopy(self.milestones)
        data["milestones"][1]["approval_decision"] = "PENDING"
        paths = [plan.AUTHORITIES["milestones"][0], plan.AUTHORITIES["milestones"][1], Path("docs/zero-trust/milestones-and-gates.md"), plan.AUTHORITIES["execution_plan"][0]]
        with copied_root(paths) as root:
            write_json(root / plan.AUTHORITIES["milestones"][0], data)
            result = plan.Result()
            plan.validate_milestones(root, result)
            self.assertTrue(failures(result, "milestones.claim"))

    def test_pending_phase_0_gate_rejected(self) -> None:
        data = copy.deepcopy(self.milestones)
        data["milestones"][0]["approval_decision"] = "PENDING"
        paths = [plan.AUTHORITIES["milestones"][0], plan.AUTHORITIES["milestones"][1], Path("docs/zero-trust/milestones-and-gates.md"), plan.AUTHORITIES["execution_plan"][0]]
        with copied_root(paths) as root:
            write_json(root / plan.AUTHORITIES["milestones"][0], data)
            result = plan.Result()
            plan.validate_milestones(root, result)
            self.assertTrue(failures(result, "milestones.claim"))

    def test_incomplete_phase_0_roadmap_rejected(self) -> None:
        data = copy.deepcopy(self.roadmap)
        data["phases"][0]["current_status"] = "IN_PROGRESS"
        paths = [plan.AUTHORITIES["roadmap"][0], plan.AUTHORITIES["roadmap"][1], Path("docs/zero-trust/final-roadmap.md")]
        with copied_root(paths) as root:
            write_json(root / plan.AUTHORITIES["roadmap"][0], data)
            result = plan.Result()
            plan.validate_roadmap(root, result)
            self.assertTrue(failures(result, "roadmap.claim"))

    def test_numbered_scenario_authority_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "active.md"
            path.write_text("S" + "001 is an active implementation authority.\n", encoding="utf-8")
            result = retirement.Result()
            retirement.validate_references(root, [Path("active.md")], result)
            self.assertGreater(result.failed, 0)

    def test_scenario_aggregate_presence_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools/scenario-aggregate.py").write_text("# retired authority\n", encoding="utf-8")
            result = retirement.Result()
            retirement.validate_retired_paths(root, result)
            self.assertGreater(result.failed, 0)

    def test_guessed_kisa_item_rejected(self) -> None:
        paths = [plan.AUTHORITIES["kisa_mapping"][0], plan.AUTHORITIES["kisa_mapping"][1], Path("docs/references/kisa-2026-critical-infrastructure-guide.yaml"), Path("docs/zero-trust/capability-catalog.yaml"), Path("docs/zero-trust/mappings/zt-kisa-technical-control-map.md")]
        with copied_root(paths) as root:
            data = plan.load(root / plan.AUTHORITIES["kisa_mapping"][0])
            data["mappings"][0]["kisa_item_code"] = "U-99"
            data["mappings"][0]["mapping_id"] = "MAP-ZT-ID-001-U-99"
            write_json(root / plan.AUTHORITIES["kisa_mapping"][0], data)
            result = plan.Result()
            plan.validate_kisa_mapping(root, result)
            self.assertTrue(failures(result, "kisa.guessed"))

    def _status_root(self):
        paths = [plan.AUTHORITIES["package_status"][0], plan.AUTHORITIES["package_status"][1], Path("docs/zero-trust/package-flow.yaml")]
        paths.extend(Path("docs/zero-trust/packages") / f"{package.lower()}-package.yaml" for package in ("ZT-DEV-001", "ZT-APP-001", "ZT-DATA-001", "ZT-SYS-001", "ZT-AUTO-001", "ZT-VIS-002"))
        return copied_root(paths)

    def test_runtime_status_divergence_rejected(self) -> None:
        with self._status_root() as root:
            data = plan.load(root / plan.AUTHORITIES["package_status"][0])
            next(item for item in data["packages"] if item["package_id"] == "ZT-ID-001")["runtime_validation_status"] = "NOT_VALIDATED"
            write_json(root / plan.AUTHORITIES["package_status"][0], data)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            result = plan.Result()
            plan.validate_status_truth(root, result)
            self.assertTrue(failures(result, "status.preservation"))

    def test_compliance_overclaim_rejected(self) -> None:
        with self._status_root() as root:
            data = plan.load(root / plan.AUTHORITIES["package_status"][0])
            data["packages"][0]["compliance_status"] = "NOT_APPLICABLE"
            write_json(root / plan.AUTHORITIES["package_status"][0], data)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            result = plan.Result()
            plan.validate_status_truth(root, result)
            self.assertTrue(failures(result, "status.claim"))

    def test_phase2_visibility_full_acceptance_overclaim_rejected(self) -> None:
        with self._status_root() as root:
            data = plan.load(root / plan.AUTHORITIES["package_status"][0])
            next(item for item in data["packages"] if item["package_id"] == "ZT-VIS-002")["runtime_acceptance_status"] = "ACCEPTED"
            write_json(root / plan.AUTHORITIES["package_status"][0], data)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            result = plan.Result()
            plan.validate_status_truth(root, result)
            self.assertTrue(failures(result, "status.phase2_visibility"))

    def test_tracked_runtime_rejected(self) -> None:
        with self._status_root() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            runtime = root / ".runtime/zero-trust/test/result.txt"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("synthetic\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", ".runtime/zero-trust/test/result.txt"], cwd=root, check=True)
            result = plan.Result()
            plan.validate_status_truth(root, result)
            self.assertTrue(failures(result, "status.runtime"))

    def test_secret_assignment_rejected(self) -> None:
        safety_paths = [path for pair in plan.AUTHORITIES.values() for path in pair] + [Path("README.md"), Path("docs/project-definition.md"), Path("docs/project-methodology.md"), Path("docs/control-validation-lifecycle.md"), Path("docs/references/kisa-2026-critical-infrastructure-guide.yaml")]
        with copied_root(safety_paths) as root:
            with (root / "README.md").open("a", encoding="utf-8") as stream:
                stream.write("pass" + "word: synthetic-secret-value\n")
            result = plan.Result()
            plan.validate_repository_safety(root, result)
            self.assertTrue(failures(result, "safety.secret"))

    def test_documentation_synchronization_rejected(self) -> None:
        paths = [plan.AUTHORITIES["roadmap"][0], plan.AUTHORITIES["roadmap"][1], Path("docs/zero-trust/final-roadmap.md")]
        with copied_root(paths) as root:
            path = root / "docs/zero-trust/final-roadmap.md"
            path.write_text(path.read_text(encoding="utf-8").replace("Phase 5", "Final assessment"), encoding="utf-8")
            result = plan.Result()
            plan.validate_roadmap(root, result)
            self.assertTrue(failures(result, "roadmap.sync"))

    def test_project_plan_validators_are_read_only(self) -> None:
        before = repository_fingerprint()
        scripts = [
            "validate_zt_project_definition.py", "validate_zt_roadmap.py", "validate_zt_execution_plan.py",
            "validate_zt_dependency_graph.py", "validate_zt_milestones.py", "validate_zt_risk_register.py",
            "validate_zt_evidence_plan.py", "validate_zt_maturity_target.py", "validate_zt_kisa_mapping.py",
            "validate_zt_package_acceptance_cases.py", "validate_zt_status_truth.py",
        ]
        for script in scripts:
            completed = subprocess.run([sys.executable, f"tools/{script}", "--strict"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual(before, repository_fingerprint())


if __name__ == "__main__":
    unittest.main()
