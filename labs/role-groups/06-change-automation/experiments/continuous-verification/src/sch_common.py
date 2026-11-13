#!/usr/bin/env python3
"""Shared deterministic controls for the bounded ZT-SCH-001 schedule."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/zero-trust/scheduled-validation-policy.yaml"
RUNTIME = ROOT / ".runtime/zero-trust/scheduled-validation"
REGISTRATION = RUNTIME / "registration.json"
STATUS = RUNTIME / "scheduler-status.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def parse_duration(value: str) -> timedelta:
    if value == "P7D": return timedelta(days=7)
    if value == "P30D": return timedelta(days=30)
    if value == "PT2H": return timedelta(hours=2)
    raise ValueError(f"unsupported bounded duration: {value}")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def schedule_fingerprint(policy: dict[str, Any]) -> str:
    return canonical_hash({key: policy[key] for key in ("selection", "scheduler", "trigger", "runtime_controls", "evidence", "retention", "artifacts")})


def execution_window_status(policy: dict[str, Any], local_now: datetime) -> tuple[str, datetime, datetime]:
    if local_now.tzinfo is None:
        raise ValueError("local execution time must include a timezone")
    hour, minute, second = (int(part) for part in str(policy["trigger"]["daily_start_time_local"]).split(":"))
    scheduled = local_now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    deadline = scheduled + parse_duration(str(policy["trigger"]["catch_up_window"]))
    if local_now < scheduled:
        return "BEFORE_DAILY_WINDOW", scheduled, deadline
    if local_now > deadline:
        return "CATCH_UP_WINDOW_EXPIRED", scheduled, deadline
    return "OPEN", scheduled, deadline


def validate_configuration(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metadata, selection = policy.get("metadata", {}), policy.get("selection", {})
    scheduler, trigger = policy.get("scheduler", {}), policy.get("trigger", {})
    controls, evidence = policy.get("runtime_controls", {}), policy.get("evidence", {})
    acceptance = policy.get("acceptance", {})
    artifacts = policy.get("artifacts", [])
    if metadata.get("package_id") != "ZT-SCH-001" or metadata.get("predecessor") != "ZT-RV-001": errors.append("package/predecessor mismatch")
    if selection != {"campaign_id":"ZT-RV-001","capability_id":"ZT-4.1.1","validator_id":"ZTCV-VAL-SYS","workflow_id":"ZT-CV-WF-001","execution_mode":"EXECUTE_READ_ONLY"}: errors.append("selection must remain the fixed accepted RV workflow")
    if scheduler.get("platform") != "WINDOWS_TASK_SCHEDULER" or scheduler.get("credential_storage") is not False: errors.append("scheduler must be Windows Task Scheduler without stored credentials")
    if scheduler.get("logon_type") != "INTERACTIVE_TOKEN" or scheduler.get("run_level") != "LIMITED": errors.append("scheduler principal must be limited interactive-token")
    if trigger.get("type") != "DAILY" or trigger.get("interval_days") != 1: errors.append("trigger must be daily")
    if trigger.get("start_when_available") is not True or trigger.get("catch_up") is not True or trigger.get("catch_up_window") != "PT2H": errors.append("bounded two-hour catch-up behavior must remain enabled")
    if controls.get("timeout_seconds") != 1200 or controls.get("child_timeout_seconds") != 900: errors.append("reviewed timeout boundary mismatch")
    if controls.get("multiple_instances") != "IGNORE_NEW" or controls.get("exclusive_lock") is not True or controls.get("one_attempt_per_local_date") is not True: errors.append("overlap controls mismatch")
    for field in ("automatic_retry", "automatic_remediation", "infrastructure_mutation", "repository_mutation", "history_auto_append", "maturity_auto_update", "phase_auto_completion"):
        if controls.get(field) is not False: errors.append(f"{field} must remain false")
    if controls.get("restart_count") != 0: errors.append("restart_count must remain zero")
    if evidence.get("runtime_root") != ".runtime/zero-trust/scheduled-validation" or evidence.get("raw_output_tracked") is not False: errors.append("runtime evidence boundary mismatch")
    if evidence.get("sanitization_required") is not True or evidence.get("scheduler_correlation_required") is not True or evidence.get("explicit_review_required") is not True: errors.append("evidence review controls must remain enabled")
    expected_paths = {
        "tools/continuous_verification/sch_common.py",
        "tools/continuous_verification/run_scheduled_validation.py",
        "tools/continuous_verification/run_repeatability_campaign.py",
        "tools/live-validation/run-scheduled-validation.ps1",
        "tools/live-validation/sanitize-live-evidence.py",
    }
    actual_paths = {str(item.get("path")) for item in artifacts if isinstance(item, dict)}
    if actual_paths != expected_paths: errors.append("scheduled execution artifact set mismatch")
    for item in artifacts:
        target = ROOT / str(item.get("path", ""))
        if not target.is_file() or item.get("sha256") != file_hash(target): errors.append(f"scheduled execution artifact drift: {item.get('path')}")
    if acceptance.get("target_continuity") != "EC5_SCHEDULED_RUNTIME" or acceptance.get("minimum_distinct_scheduled_dates") != 3: errors.append("EC5 requires three distinct scheduled dates")
    return errors


def expected_due_dates(registration: dict[str, Any], policy: dict[str, Any], now: datetime) -> list[str]:
    first = parse_time(str(registration["first_scheduled_run"]))
    local_now = now.astimezone(first.tzinfo)
    grace = parse_duration(policy["evidence"]["missed_run_grace"])
    dates: list[str] = []
    cursor = first
    while cursor + grace <= local_now:
        dates.append(cursor.date().isoformat())
        cursor += timedelta(days=1)
    return dates


def assess(records: list[dict[str, Any]], registration: dict[str, Any] | None, policy: dict[str, Any], now: datetime) -> dict[str, Any]:
    due = expected_due_dates(registration, policy, now) if registration else []
    observed = {str(item.get("scheduled_date_local")) for item in records}
    successful = [item for item in records if item.get("result") == "PASS" and item.get("exit_code") == 0 and item.get("sanitization_status") == "PASS"]
    verified = [item for item in successful if item.get("trigger_verification") == "VERIFIED_SCHEDULER_CORRELATION"]
    successful_dates = sorted({str(item.get("scheduled_date_local")) for item in successful})
    verified_dates = sorted({str(item.get("scheduled_date_local")) for item in verified})
    failures = [str(item.get("execution_id")) for item in records if item not in successful]
    missed = sorted(set(due) - observed)
    latest = max((parse_time(str(item["started_at"])) for item in successful), default=None)
    freshness = "NOT_APPLICABLE" if latest is None else "FRESH" if now.astimezone(timezone.utc) - latest.astimezone(timezone.utc) <= parse_duration(policy["evidence"]["freshness_window"]) else "STALE"
    required = int(policy["acceptance"]["minimum_distinct_scheduled_dates"])
    acceptance_window = due[-required:] if len(due) >= required else due
    window_complete = len(acceptance_window) == required
    window_missed = sorted(set(acceptance_window) - observed)
    eligible = window_complete and all(day in verified_dates for day in acceptance_window) and freshness == "FRESH"
    candidate = window_complete and all(day in successful_dates for day in acceptance_window) and freshness == "FRESH"
    return {
        "package_id": "ZT-SCH-001", "schedule_id": policy["metadata"]["schedule_id"],
        "assessment_time": iso(now), "installed": registration is not None,
        "execution_count": len(records), "successful_count": len(successful),
        "successful_distinct_scheduled_dates": len(successful_dates), "successful_dates": successful_dates,
        "verified_successful_count": len(verified), "verified_distinct_scheduled_dates": len(verified_dates), "verified_dates": verified_dates,
        "failed_execution_ids": failures, "missed_scheduled_dates": missed,
        "acceptance_window_dates": acceptance_window, "acceptance_window_missed_dates": window_missed,
        "freshness": freshness, "current_continuity": "EC5_SCHEDULED_RUNTIME" if eligible else "EC4_REPEATABLE_RUNTIME",
        "acceptance_candidate": "ELIGIBLE_FOR_EXPLICIT_REVIEW" if eligible else "ELIGIBLE_FOR_CORRELATION_REVIEW" if candidate else "NOT_ELIGIBLE",
        "authoritative_update_performed": False,
        "limitations": ["Runtime records are ignored candidates until scheduler correlation and explicit evidence review are complete."]
    }
