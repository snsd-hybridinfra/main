#!/usr/bin/env python3
"""Shared deterministic calculations for the bounded ZT-CV-001 package."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ZT = ROOT / "policy"
RUNTIME = ROOT / ".runtime/continuous-verification/latest"

PATHS = {
    "policy": ZT / "continuous-verification-policy.yaml",
    "freshness": ZT / "evidence-freshness-policy.yaml",
    "capabilities": ZT / "capability-acceptance-catalog.yaml",
    "gates": ZT / "package-acceptance-gates.yaml",
    "regressions": ZT / "verification-regression-policy.yaml",
    "exceptions": ZT / "verification-exception-policy.yaml",
    "maturity": ZT / "maturity-reassessment-policy.yaml",
    "history": ZT / "verification-history.yaml",
}

CONTINUITY_ORDER = {
    "EC0_NONE": 0, "EC1_DESIGN": 1, "EC2_CONFIGURATION": 2,
    "EC3_ONE_TIME_RUNTIME": 3, "EC4_REPEATABLE_RUNTIME": 4,
    "EC5_SCHEDULED_RUNTIME": 5, "EC6_CONTINUOUS_OBSERVATION": 6,
    "EC7_CONTINUOUS_ENFORCEMENT": 7,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def parse_duration(value: str) -> timedelta:
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", value)
    if not match or not any(match.groups()):
        raise ValueError(f"unsupported ISO-8601 duration: {value}")
    days, hours, minutes = (int(item or 0) for item in match.groups())
    return timedelta(days=days, hours=hours, minutes=minutes)


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".json", ".md", ".txt", ".yaml", ".yml"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def freshness_results(history: dict[str, Any], policy: dict[str, Any], assessment_time: datetime) -> list[dict[str, Any]]:
    policies = {item["id"]: item for item in policy.get("policies", [])}
    results: list[dict[str, Any]] = []
    for record in history.get("executions", []):
        policy_id = record.get("freshness_policy_id")
        selected = policies.get(policy_id)
        state = "UNKNOWN"
        reason = "UNRESOLVED_FRESHNESS_POLICY"
        age_seconds: int | None = None
        if selected:
            try:
                observed = parse_time(str(record.get("execution_date", "")))
                age = assessment_time - observed
                age_seconds = int(age.total_seconds())
                if age.total_seconds() < 0:
                    state, reason = "UNKNOWN", "FUTURE_TIMESTAMP"
                elif age <= parse_duration(selected["freshness_window"]):
                    state, reason = "FRESH", "WITHIN_FRESHNESS_WINDOW"
                elif age <= parse_duration(selected["freshness_window"]) + parse_duration(selected["grace_period"]):
                    state, reason = "AGING", "WITHIN_GRACE_PERIOD"
                elif age <= parse_duration(selected["expiration_window"]):
                    state, reason = "STALE", "PAST_GRACE_BEFORE_EXPIRATION"
                else:
                    state, reason = "EXPIRED", "PAST_EXPIRATION_WINDOW"
            except (TypeError, ValueError, KeyError) as exc:
                reason = f"MALFORMED_FRESHNESS_INPUT:{exc}"
        results.append({
            "execution_id": record.get("execution_id"), "package_id": record.get("package_id"),
            "policy_id": policy_id, "execution_date": record.get("execution_date"),
            "assessment_time": iso(assessment_time), "age_seconds": age_seconds,
            "freshness_status": state, "reason": reason,
        })
    return results


def execution_success(record: dict[str, Any]) -> bool:
    return (
        record.get("result") in {"PASS", "WARN"}
        and int(record.get("fail", 0)) == 0
        and record.get("sanitization_status") == "PASS"
    )


def repeatability_results(history: dict[str, Any], freshness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    freshness_map = {item["execution_id"]: item["freshness_status"] for item in freshness}
    groups: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for record in history.get("executions", []):
        key = (
            str(record.get("package_id")), str(record.get("validator_id")),
            str(record.get("validator_version")), str(record.get("workflow_id")),
            str(record.get("execution_scope")), str(record.get("plan_hash")),
        )
        groups.setdefault(key, []).append(record)
    results: list[dict[str, Any]] = []
    for key, records in sorted(groups.items()):
        ordered = sorted(records, key=lambda item: str(item.get("execution_date", "")))
        ids = [str(item.get("execution_id")) for item in ordered]
        successes = [item for item in ordered if execution_success(item)]
        unique = len(ids) == len(set(ids))
        current = [item for item in successes if freshness_map.get(item.get("execution_id")) in {"FRESH", "AGING"}]
        continuity = "EC0_NONE"
        reasons: list[str] = []
        if successes:
            continuity = "EC3_ONE_TIME_RUNTIME"
        stable_plan = key[5] not in {"", "None", "NOT_RECORDED"}
        independent = unique and len(successes) >= 3
        consecutive = len(successes) == len(ordered[-len(successes):]) if successes else False
        if independent and consecutive and stable_plan and len(current) >= 3:
            continuity = "EC4_REPEATABLE_RUNTIME"
        dates = {str(item.get("execution_date", ""))[:10] for item in successes if item.get("scheduled_trigger") is True}
        if continuity == "EC4_REPEATABLE_RUNTIME" and len(dates) >= 3 and all(item.get("scheduled_trigger") is True for item in successes[-3:]):
            continuity = "EC5_SCHEDULED_RUNTIME"
        if len(successes) < 3:
            reasons.append("FEWER_THAN_THREE_SUCCESSFUL_EXECUTIONS")
        if not stable_plan:
            reasons.append("STABLE_PLAN_HASH_NOT_RECORDED")
        if not unique:
            reasons.append("DUPLICATE_EXECUTION_ID")
        if any(not execution_success(item) for item in ordered):
            reasons.append("NON_SUCCESSFUL_EXECUTION_IN_SEQUENCE")
        if continuity != "EC5_SCHEDULED_RUNTIME":
            reasons.append("THREE_DISTINCT_SCHEDULED_DATES_NOT_PROVEN")
        results.append({
            "group": {"package_id": key[0], "validator_id": key[1], "validator_version": key[2],
                      "workflow_id": key[3], "execution_scope": key[4], "plan_hash": key[5]},
            "execution_ids": ids, "execution_count": len(ordered), "successful_count": len(successes),
            "current_successful_count": len(current), "unique_execution_ids": unique,
            "independent_successes": independent, "consecutive_successes": consecutive,
            "scheduled_distinct_dates": len(dates), "evidence_continuity": continuity,
            "limitations": reasons,
        })
    return results


def package_acceptance_results(gates: dict[str, Any], history: dict[str, Any], freshness: list[dict[str, Any]], repeatability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: dict[str, list[dict[str, Any]]] = {}
    for record in history.get("executions", []):
        records.setdefault(str(record.get("package_id")), []).append(record)
    freshness_map = {item["execution_id"]: item["freshness_status"] for item in freshness}
    continuity: dict[str, str] = {}
    for item in repeatability:
        package_id = item["group"]["package_id"]
        current = continuity.get(package_id, "EC0_NONE")
        if CONTINUITY_ORDER[item["evidence_continuity"]] > CONTINUITY_ORDER[current]:
            continuity[package_id] = item["evidence_continuity"]
    output: list[dict[str, Any]] = []
    for gate in gates.get("gates", []):
        package_id = gate["package_id"]
        package_records = sorted(records.get(package_id, []), key=lambda item: str(item.get("execution_date", "")))
        latest = package_records[-1] if package_records else None
        findings: list[str] = []
        missing = [item for item in gate.get("required_evidence_files", []) if not (ROOT / item).is_file()]
        if missing:
            findings.append("REQUIRED_EVIDENCE_MISSING")
        if latest is None:
            state = "REVIEW_REQUIRED"
            findings.append("NO_RUNTIME_HISTORY")
        elif not execution_success(latest):
            state = "NOT_ACCEPTED"
            findings.append("LATEST_EXECUTION_FAILED")
        elif latest.get("execution_authority") not in gate.get("required_evidence_authority", []):
            state = "REVIEW_REQUIRED"
            findings.append("EVIDENCE_AUTHORITY_NOT_ACCEPTED")
        elif freshness_map.get(latest.get("execution_id")) == "EXPIRED":
            state = "ACCEPTANCE_EXPIRED"
            findings.append("LATEST_EVIDENCE_EXPIRED")
        elif freshness_map.get(latest.get("execution_id")) in {"STALE", "UNKNOWN", None}:
            state = "REVIEW_REQUIRED"
            findings.append("LATEST_EVIDENCE_NOT_FRESH")
        elif int(latest.get("warn", 0)) > int(gate.get("allowed_warnings", 0)):
            state = "REVIEW_REQUIRED"
            findings.append("WARNING_BUDGET_EXCEEDED")
        else:
            state = gate.get("acceptance_state", "REVIEW_REQUIRED")
        if missing:
            state = "REVIEW_REQUIRED"
        output.append({
            "gate_id": gate["id"], "package_id": package_id, "assessment_state": state,
            "configured_state": gate.get("acceptance_state"), "latest_execution_id": latest.get("execution_id") if latest else None,
            "freshness_status": freshness_map.get(latest.get("execution_id")) if latest else "MISSING",
            "evidence_continuity": continuity.get(package_id, "EC0_NONE"),
            "missing_evidence": missing, "findings": findings,
            "authoritative_update_performed": False,
        })
    return output


def capability_acceptance_results(catalog: dict[str, Any], history: dict[str, Any], freshness: list[dict[str, Any]], repeatability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    freshness_map = {item["execution_id"]: item["freshness_status"] for item in freshness}
    records = history.get("executions", [])
    continuity_by_validator: dict[str, str] = {}
    for item in repeatability:
        validator = item["group"]["validator_id"]
        previous = continuity_by_validator.get(validator, "EC0_NONE")
        if CONTINUITY_ORDER[item["evidence_continuity"]] > CONTINUITY_ORDER[previous]:
            continuity_by_validator[validator] = item["evidence_continuity"]
    results: list[dict[str, Any]] = []
    for capability in catalog.get("capabilities", []):
        validators = set(capability.get("required_validators", []))
        relevant = [item for item in records if item.get("validator_id") in validators and capability["id"] in item.get("capability_ids", [])]
        latest = sorted(relevant, key=lambda item: str(item.get("execution_date", "")))[-1] if relevant else None
        state = capability.get("acceptance_state", "REVIEW_REQUIRED")
        findings: list[str] = []
        if not latest:
            state = "REVIEW_REQUIRED"; findings.append("NO_MATCHING_RUNTIME_HISTORY")
        elif not execution_success(latest):
            state = "NOT_ACCEPTED"; findings.append("LATEST_EXECUTION_FAILED")
        elif freshness_map.get(latest.get("execution_id")) not in {"FRESH", "AGING"}:
            state = "REVIEW_REQUIRED"; findings.append("LATEST_EVIDENCE_NOT_CURRENT")
        continuity = max((continuity_by_validator.get(item, "EC0_NONE") for item in validators), key=lambda value: CONTINUITY_ORDER[value], default="EC0_NONE")
        results.append({
            "capability_id": capability["id"], "assessment_state": state,
            "configured_state": capability.get("acceptance_state"),
            "latest_execution_id": latest.get("execution_id") if latest else None,
            "freshness_status": freshness_map.get(latest.get("execution_id")) if latest else "MISSING",
            "evidence_continuity": continuity, "current_maturity": capability.get("current_maturity", "UNASSESSED"),
            "confidence": capability.get("confidence", "LOW"), "findings": findings,
            "limitations": capability.get("limitations", []), "authoritative_update_performed": False,
        })
    return results


def regression_results(history: dict[str, Any], freshness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    freshness_map = {item["execution_id"]: item["freshness_status"] for item in freshness}
    freshness_reason = {item["execution_id"]: item.get("reason") for item in freshness}
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    records = history.get("executions", [])
    latest_by_stream: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        if freshness_reason.get(record.get("execution_id")) == "FUTURE_TIMESTAMP":
            continue
        key = (
            str(record.get("package_id")),
            str(record.get("validator_id")),
            str(record.get("execution_scope")),
        )
        previous = latest_by_stream.get(key)
        if previous is None or str(record.get("execution_date", "")) > str(previous.get("execution_date", "")):
            latest_by_stream[key] = record
    current_ids = {str(record.get("execution_id")) for record in latest_by_stream.values()}
    for record in records:
        execution_id = str(record.get("execution_id"))
        if execution_id in seen:
            findings.append({"type":"DEPENDENCY_REGRESSION","execution_id":execution_id,"severity":"HIGH","reason":"DUPLICATE_EXECUTION_ID"})
        seen.add(execution_id)
        if not execution_success(record):
            findings.append({"type":"VALIDATION_REGRESSION","execution_id":execution_id,"severity":"HIGH","reason":"FAILED_OR_UNSANITIZED_EXECUTION"})
        if execution_id in current_ids and freshness_map.get(execution_id) in {"STALE", "EXPIRED", "UNKNOWN"}:
            findings.append({"type":"EVIDENCE_FRESHNESS_REGRESSION","execution_id":execution_id,"severity":"HIGH","reason":freshness_map.get(execution_id)})
        for relative, expected in record.get("evidence_hashes", {}).items():
            path = ROOT / relative
            if not path.is_file():
                findings.append({"type":"IMPLEMENTATION_REGRESSION","execution_id":execution_id,"severity":"HIGH","reason":f"MISSING:{relative}"})
            elif sha256_file(path) != expected:
                findings.append({"type":"CONFIGURATION_DRIFT","execution_id":execution_id,"severity":"HIGH","reason":f"HASH_CHANGED:{relative}"})
    return findings


def maturity_results(capability_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "capability_id": item["capability_id"], "source_maturity": item.get("current_maturity", "UNASSESSED"),
        "candidate_maturity": item.get("current_maturity", "UNASSESSED"), "decision": "RETAIN",
        "reason": "EC4_REPEATABLE_RUNTIME_AND_CAPABILITY_SPECIFIC_SOURCE_TABLE_REVIEW_NOT_PROVEN",
        "evidence_continuity": item.get("evidence_continuity", "EC0_NONE"),
        "authoritative_update_performed": False,
    } for item in capability_results]
