"""Regression tests for the fixed-handler ZT-AUTO-001 foundation."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "tools/automation"
sys.path.insert(0, str(AUTO))
from automation_common import ACTION_PATH, POLICY_PATH, WORKFLOW_PATH, build_plan, load, policy_decision, unsafe_parameters, validate_catalogs  # noqa: E402


class ZtAuto001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = load(ACTION_PATH)
        self.workflows = load(WORKFLOW_PATH)
        self.policy = load(POLICY_PATH)
        catalog = load(ROOT / "docs/zero-trust/capability-catalog.yaml")
        self.capability_ids = {item["id"] for item in catalog["capabilities"]}

    def errors(self, actions=None, workflows=None, policy=None):
        return validate_catalogs(actions or self.actions, workflows or self.workflows, policy or self.policy, self.capability_ids)

    def test_valid_catalogs(self): self.assertEqual([], self.errors())
    def test_duplicate_action_id_fails(self):
        value=copy.deepcopy(self.actions); value["actions"].append(copy.deepcopy(value["actions"][0])); self.assertTrue(any("Action IDs" in item for item in self.errors(actions=value)))
    def test_duplicate_workflow_id_fails(self):
        value=copy.deepcopy(self.workflows); value["workflows"].append(copy.deepcopy(value["workflows"][0])); self.assertTrue(any("Workflow IDs" in item for item in self.errors(workflows=value)))
    def test_invalid_action_type_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["action_type"]="EXECUTE_SHELL"; self.assertTrue(any("invalid action type" in item for item in self.errors(actions=value)))
    def test_unknown_capability_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["capability_mappings"]=["ZT-TEST-999"]; self.assertTrue(any("unknown capability" in item for item in self.errors(actions=value)))
    def test_arbitrary_handler_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["implementation"]="TEST_FIXTURE_PROHIBITED_ACTION"; self.assertTrue(any("not registered" in item for item in self.errors(actions=value)))
    def test_arbitrary_command_field_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["command"]="TEST_FIXTURE"; self.assertTrue(any("arbitrary execution field" in item for item in self.errors(actions=value)))
    def test_shell_field_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["shell"]=True; self.assertTrue(any("arbitrary execution field" in item for item in self.errors(actions=value)))
    def test_missing_timeout_fails(self):
        value=copy.deepcopy(self.actions); value["actions"][0]["timeout_seconds"]=0; self.assertTrue(any("invalid timeout" in item for item in self.errors(actions=value)))
    def test_mutation_action_enabled_fails(self):
        value=copy.deepcopy(self.actions); target=next(item for item in value["actions"] if item["id"]=="ZTA-ACT-REF-001"); target["executable"]=True; self.assertTrue(any("must not be executable" in item for item in self.errors(actions=value)))
    def test_unresolved_action_fails(self):
        value=copy.deepcopy(self.workflows); value["workflows"][0]["steps"][0]["action_id"]="ZTA-ACT-TEST-MISSING"; self.assertTrue(any("unresolved action" in item for item in self.errors(workflows=value)))
    def test_circular_dependency_fails(self):
        value=copy.deepcopy(self.workflows); steps=value["workflows"][0]["steps"]; steps[0]["depends_on"]=[steps[-1]["step_id"]]; self.assertTrue(any("cycle" in item for item in self.errors(workflows=value)))
    def test_unknown_condition_fails(self):
        value=copy.deepcopy(self.workflows); value["workflows"][0]["steps"][0]["condition"]="PYTHON_EXPRESSION"; self.assertTrue(any("unknown condition" in item for item in self.errors(workflows=value)))
    def test_default_deny_fails_when_changed(self):
        value=copy.deepcopy(self.policy); value["metadata"]["default_decision"]="ALLOW"; self.assertTrue(any("default to DENY" in item for item in self.errors(policy=value)))
    def test_deterministic_plan_hash(self):
        first=build_plan("ZTA-WF-VAL-001","PLAN",self.actions,self.workflows); second=build_plan("ZTA-WF-VAL-001","PLAN",self.actions,self.workflows); self.assertEqual(first,second)
    def test_check_policy_allowed(self):
        plan=build_plan("ZTA-WF-VAL-001","CHECK",self.actions,self.workflows); self.assertEqual("ALLOW_CHECK",policy_decision(plan,"CHECK")[0])
    def test_r3_policy_allowed(self):
        plan=build_plan("ZTA-WF-VAL-001","EXECUTE_READ_ONLY",self.actions,self.workflows); self.assertEqual("ALLOW_EXECUTE_READ_ONLY",policy_decision(plan,"EXECUTE_READ_ONLY")[0])
    def test_r5_execution_denied(self):
        plan=build_plan("ZTA-WF-VAL-001","EXECUTE_READ_ONLY",self.actions,self.workflows); plan["effective_risk"]="R5_SERVICE_AFFECTING"; self.assertEqual("DENY",policy_decision(plan,"EXECUTE_READ_ONLY")[0])
    def test_r8_execution_denied(self):
        plan=build_plan("ZTA-WF-VAL-001","EXECUTE_READ_ONLY",self.actions,self.workflows); plan["effective_risk"]="R8_DESTRUCTIVE"; self.assertEqual("DENY",policy_decision(plan,"EXECUTE_READ_ONLY")[0])
    def test_proposal_requires_approval(self):
        plan=build_plan("ZTA-WF-GAP-001","PROPOSAL_ONLY",self.actions,self.workflows); self.assertEqual("REQUIRE_APPROVAL",policy_decision(plan,"PROPOSAL_ONLY")[0])
    def test_expired_approval_rejected(self):
        plan=build_plan("ZTA-WF-GAP-001","PROPOSAL_ONLY",self.actions,self.workflows); approval={"workflow_id":plan["workflow_id"],"plan_hash":plan["plan_hash"],"approved_execution_mode":"PROPOSAL_ONLY","expiration":"2000-01-01T00:00:00Z"}; self.assertEqual("DENY",policy_decision(plan,"PROPOSAL_ONLY",approval)[0])
    def test_plan_hash_mismatch_rejected(self):
        plan=build_plan("ZTA-WF-GAP-001","PROPOSAL_ONLY",self.actions,self.workflows); approval={"workflow_id":plan["workflow_id"],"plan_hash":"0"*64,"approved_execution_mode":"PROPOSAL_ONLY","expiration":"2099-01-01T00:00:00Z"}; self.assertEqual("DENY",policy_decision(plan,"PROPOSAL_ONLY",approval)[0])
    def test_approved_enum_parameter_passes(self): self.assertEqual([],unsafe_parameters({"mode":"CHECK"}))
    def test_path_traversal_fails(self): self.assertTrue(unsafe_parameters({"path":"../TEST_FIXTURE"}))
    def test_shell_metacharacter_fails(self): self.assertTrue(unsafe_parameters({"value":"SAFE;TEST"}))
    def test_absolute_path_fails(self): self.assertTrue(unsafe_parameters({"path":"C:\\TEST_FIXTURE"}))
    def test_unc_path_fails(self): self.assertTrue(unsafe_parameters({"path":"\\\\TEST\\SHARE"}))
    def test_check_mode_performs_no_action(self):
        before=set((ROOT/".runtime/zero-trust/automation/locks").glob("*")) if (ROOT/".runtime/zero-trust/automation/locks").exists() else set()
        result=subprocess.run([sys.executable,str(AUTO/"run_workflow.py"),"--check","--workflow","ZTA-WF-VAL-001"],cwd=ROOT,capture_output=True,text=True,check=False)
        after=set((ROOT/".runtime/zero-trust/automation/locks").glob("*")) if (ROOT/".runtime/zero-trust/automation/locks").exists() else set()
        self.assertEqual(0,result.returncode); self.assertEqual(before,after)
    def test_source_has_no_dynamic_execution_primitives(self):
        text=(AUTO/"run_workflow.py").read_text(encoding="utf-8")
        self.assertNotIn("shell=True",text); self.assertNotIn("Invoke-Expression",text); self.assertNotIn("ssh root@",text)
    def test_runtime_is_ignored(self):
        result=subprocess.run(["git","check-ignore",".runtime/zero-trust/automation/test"],cwd=ROOT,capture_output=True,text=True,check=False); self.assertEqual(0,result.returncode)
    def test_fixture_catalog_is_inert(self):
        value=load(ROOT/"tests/fixtures/zt-auto-001/fixture-catalog.yaml"); self.assertEqual("TEST_FIXTURE_ONLY_NON_EXECUTABLE",value["fixture_scope"]); self.assertGreaterEqual(len(value["fixtures"]),18)


if __name__ == "__main__": unittest.main()
