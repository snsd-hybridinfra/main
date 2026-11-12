#!/usr/bin/env python3
"""Shared, dependency-free catalog, policy, and deterministic-plan helpers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = ROOT / "policy/automation-action-catalog.yaml"
WORKFLOW_PATH = ROOT / "policy/automation-workflow-catalog.yaml"
POLICY_PATH = ROOT / "policy/automation-approval-policy.yaml"

RISK_ORDER = {
    "R0_READ_ONLY": 0, "R1_LOCAL_ARTIFACT_WRITE": 1,
    "R2_REPOSITORY_STATUS_PROPOSAL": 2, "R3_REMOTE_READ_ONLY": 3,
    "R4_LOW_RISK_CONFIGURATION": 4, "R5_SERVICE_AFFECTING": 5,
    "R6_NETWORK_AFFECTING": 6, "R7_ACCESS_AFFECTING": 7,
    "R8_DESTRUCTIVE": 8,
}
APPROVAL_ORDER = {
    "APPROVAL_NONE": 0, "APPROVAL_POLICY": 1, "APPROVAL_OPERATOR": 2,
    "APPROVAL_SECURITY_REVIEW": 3, "APPROVAL_CHANGE_CONTROL": 4,
    "APPROVAL_EXPLICIT_USER": 5, "APPROVAL_PROHIBITED": 6,
}
ACTION_TYPES = {
    "LOCAL_VALIDATION", "REMOTE_READ_ONLY_VALIDATION", "EVIDENCE_COLLECTION",
    "EVIDENCE_SANITIZATION", "SCHEMA_VALIDATION", "CORRELATION",
    "REPORT_GENERATION", "STATUS_PROPOSAL", "NOTIFICATION_PROPOSAL",
    "INCIDENT_HANDOFF", "CONFIGURATION_PROPOSAL", "PROHIBITED_REFERENCE",
}
MODES = {"CHECK", "PLAN", "EXECUTE_READ_ONLY", "PROPOSAL_ONLY", "PROHIBITED"}
CONDITIONS = {
    "ALWAYS", "PREVIOUS_PASS", "PREVIOUS_PASS_OR_WARN", "PREVIOUS_FAIL",
    "FILE_EXISTS", "RESULT_EQUALS", "RESULT_NOT_EQUALS",
    "ALL_DEPENDENCIES_PASS", "ANY_DEPENDENCY_FAIL",
}
HANDLERS = {
    "validate_zero_trust", "check_zero_trust_sync", "validate_system_inventory",
    "check_system_drift", "validate_service_state", "validate_systems_live",
    "validate_telemetry_sources", "write_automation_summary", "write_gap_proposal",
    "write_correlation_review", "write_incident_review", "NONE",
    "validate_cv_configuration", "evaluate_evidence_freshness", "assess_repeatability",
    "assess_package_acceptance", "assess_capability_acceptance", "detect_regressions",
    "reassess_maturity",
}
UNSAFE_VALUE = re.compile(r"(?:\.\.|[|;`<>]|&&|\|\||\$\(|[\r\n])")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def ids(items: list[dict[str, Any]], key: str = "id") -> list[str]:
    return [str(item.get(key, "")) for item in items if isinstance(item, dict)]


def topological_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps", [])
    by_id = {item.get("step_id"): item for item in steps if isinstance(item, dict)}
    if len(by_id) != len(steps) or None in by_id or "" in by_id:
        raise ValueError("Workflow step IDs must be unique and non-empty")
    ordered: list[dict[str, Any]] = []
    pending = set(by_id)
    while pending:
        ready = sorted(step_id for step_id in pending if set(by_id[step_id].get("depends_on", [])) <= {item["step_id"] for item in ordered})
        if not ready:
            raise ValueError("Workflow step dependencies contain a cycle or unresolved reference")
        for step_id in ready:
            for dependency in by_id[step_id].get("depends_on", []):
                if dependency not in by_id:
                    raise ValueError(f"Unknown step dependency: {dependency}")
            ordered.append(by_id[step_id])
            pending.remove(step_id)
    return ordered


def validate_catalogs(actions: dict[str, Any], workflows: dict[str, Any], policy: dict[str, Any], capability_ids: set[str]) -> list[str]:
    errors: list[str] = []
    action_items = actions.get("actions", [])
    workflow_items = workflows.get("workflows", [])
    action_ids = ids(action_items)
    workflow_ids = ids(workflow_items)
    if len(action_ids) != len(set(action_ids)):
        errors.append("Action IDs must be unique")
    if len(workflow_ids) != len(set(workflow_ids)):
        errors.append("Workflow IDs must be unique")
    action_map = {item.get("id"): item for item in action_items if isinstance(item, dict)}
    forbidden_fields = {"command", "raw_command", "executable_path", "ssh_target", "remote_command", "shell"}
    for action in action_items:
        action_id = action.get("id", "<missing>")
        if action.get("action_type") not in ACTION_TYPES:
            errors.append(f"{action_id}: invalid action type")
        if action.get("implementation") not in HANDLERS:
            errors.append(f"{action_id}: arbitrary handler is not registered")
        if forbidden_fields & set(action):
            errors.append(f"{action_id}: prohibited arbitrary execution field")
        if action.get("risk_level") not in RISK_ORDER or action.get("approval_level") not in APPROVAL_ORDER:
            errors.append(f"{action_id}: invalid risk or approval level")
        if not isinstance(action.get("timeout_seconds"), int) or not 1 <= action.get("timeout_seconds", 0) <= 1200:
            errors.append(f"{action_id}: invalid timeout")
        if action.get("retry_policy") not in {"NONE", "FIXED_COUNT_READ_ONLY"}:
            errors.append(f"{action_id}: invalid retry policy")
        if RISK_ORDER.get(action.get("risk_level"), 9) >= 4 and action.get("executable") is not False:
            errors.append(f"{action_id}: mutation-class action must not be executable")
        if action.get("action_type") == "PROHIBITED_REFERENCE" and action.get("implementation") != "NONE":
            errors.append(f"{action_id}: prohibited reference has a handler")
        if any(item not in capability_ids for item in action.get("capability_mappings", [])):
            errors.append(f"{action_id}: unknown capability mapping")
        for parameter in action.get("allowed_parameters", []):
            if not isinstance(parameter, dict) or not {"name", "type", "required", "sensitive", "logging"} <= set(parameter):
                errors.append(f"{action_id}: invalid parameter contract")
            default = parameter.get("default") if isinstance(parameter, dict) else None
            if isinstance(default, str) and UNSAFE_VALUE.search(default):
                errors.append(f"{action_id}: unsafe parameter default")
    for workflow in workflow_items:
        workflow_id = workflow.get("id", "<missing>")
        if workflow.get("execution_mode") not in MODES:
            errors.append(f"{workflow_id}: invalid execution mode")
        if workflow.get("risk_level") not in RISK_ORDER or workflow.get("approval_level") not in APPROVAL_ORDER:
            errors.append(f"{workflow_id}: invalid risk or approval level")
        if any(item not in capability_ids for item in workflow.get("capability_mappings", [])):
            errors.append(f"{workflow_id}: unknown capability mapping")
        step_ids = ids(workflow.get("steps", []), "step_id")
        if len(step_ids) != len(set(step_ids)):
            errors.append(f"{workflow_id}: duplicate step ID")
        for step in workflow.get("steps", []):
            if step.get("action_id") not in action_map:
                errors.append(f"{workflow_id}: unresolved action {step.get('action_id')}")
            if step.get("condition") not in CONDITIONS:
                errors.append(f"{workflow_id}: unknown condition {step.get('condition')}")
            if any(dependency not in step_ids for dependency in step.get("depends_on", [])):
                errors.append(f"{workflow_id}: unresolved step dependency")
        try:
            topological_steps(workflow)
        except ValueError as exc:
            errors.append(f"{workflow_id}: {exc}")
    if policy.get("metadata", {}).get("default_decision") != "DENY":
        errors.append("Approval policy must default to DENY")
    contract = policy.get("approval_record_contract", {})
    required = {"approval_id", "workflow_id", "plan_hash", "approved_execution_mode", "approver_role", "approval_timestamp", "expiration", "scope", "limitations"}
    if not required <= set(contract.get("required_fields", [])) or contract.get("changed_plan_authorized") is not False:
        errors.append("Approval contract must bind all required fields and reject changed plans")
    return errors


def build_plan(workflow_id: str, mode: str, actions: dict[str, Any], workflows: dict[str, Any]) -> dict[str, Any]:
    action_map = {item["id"]: item for item in actions["actions"]}
    workflow = next((item for item in workflows["workflows"] if item.get("id") == workflow_id), None)
    if workflow is None:
        raise ValueError(f"Unknown workflow: {workflow_id}")
    ordered = topological_steps(workflow)
    plan_steps = []
    for step in ordered:
        action = action_map[step["action_id"]]
        plan_steps.append({
            "step_id": step["step_id"], "action_id": action["id"],
            "handler_id": action["implementation"], "depends_on": sorted(step.get("depends_on", [])),
            "condition": step["condition"], "risk_level": action["risk_level"],
            "approval_level": action["approval_level"], "timeout_seconds": action["timeout_seconds"],
            "retry_policy": action["retry_policy"], "working_directory": action["working_directory"],
            "evidence_required": step["evidence_required"], "rollback_type": action["rollback_type"],
        })
    effective_risk = max((item["risk_level"] for item in plan_steps), key=lambda value: RISK_ORDER[value])
    required_approval = max((item["approval_level"] for item in plan_steps), key=lambda value: APPROVAL_ORDER[value])
    body = {
        "plan_version": "1.0.0", "workflow_id": workflow_id,
        "workflow_catalog_version": workflows["metadata"]["catalog_version"],
        "action_catalog_version": actions["metadata"]["catalog_version"],
        "execution_mode": mode, "effective_risk": effective_risk,
        "required_approval": required_approval, "timeout_seconds": workflow["timeout_seconds"],
        "concurrency_policy": workflow["concurrency_policy"], "steps": plan_steps,
        "expected_evidence": sorted(workflow.get("outputs", [])), "rollback": workflow.get("rollback", {}),
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {**body, "plan_hash": hashlib.sha256(encoded).hexdigest()}


def unsafe_parameters(parameters: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for name, value in parameters.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name):
            errors.append(f"Unsafe parameter name: {name}")
        if not isinstance(value, (str, int, bool)):
            errors.append(f"Unsupported parameter type: {name}")
        elif isinstance(value, str) and (UNSAFE_VALUE.search(value) or value.startswith(("\\\\", "/")) or re.match(r"^[A-Za-z]:", value)):
            errors.append(f"Unsafe parameter value: {name}")
    return errors


def policy_decision(plan: dict[str, Any], mode: str, approval: dict[str, Any] | None = None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    risk = RISK_ORDER[plan["effective_risk"]]
    if mode in {"CHECK", "PLAN"}:
        return ("ALLOW_CHECK" if mode == "CHECK" else "ALLOW_PLAN"), reasons
    if risk >= 4:
        return "DENY", ["R4 through R8 actions cannot execute in ZT-AUTO-001"]
    if mode == "EXECUTE_READ_ONLY" and risk <= 3:
        if plan["required_approval"] in {"APPROVAL_NONE", "APPROVAL_POLICY"}:
            return "ALLOW_EXECUTE_READ_ONLY", reasons
    if mode == "PROPOSAL_ONLY" and risk <= 2:
        if plan["required_approval"] in {"APPROVAL_NONE", "APPROVAL_POLICY"}:
            return "ALLOW_PROPOSAL_ONLY", reasons
    if approval is None:
        return "REQUIRE_APPROVAL", ["A plan-bound approval record is required"]
    if approval.get("workflow_id") != plan["workflow_id"] or approval.get("plan_hash") != plan["plan_hash"]:
        return "DENY", ["Approval workflow or plan hash mismatch"]
    if approval.get("approved_execution_mode") != mode:
        return "DENY", ["Approval execution mode mismatch"]
    expiration = str(approval.get("expiration", ""))
    if expiration < "2026-07-22T00:00:00Z":
        return "DENY", ["Approval is expired"]
    return ("ALLOW_PROPOSAL_ONLY" if mode == "PROPOSAL_ONLY" else "ALLOW_EXECUTE_READ_ONLY"), reasons
