#!/usr/bin/env python3
"""Correlate one ignored ZT-SCH-001 candidate with sanitized Task Scheduler status."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timezone
from pathlib import Path

from sch_common import POLICY, REGISTRATION, ROOT, RUNTIME, STATUS, execution_window_status, file_hash, iso, load, parse_time, schedule_fingerprint, utcnow, validate_configuration, write


def correlation_errors(record: dict, status: dict, registration: dict, policy: dict) -> list[str]:
    errors = validate_configuration(policy)
    if record.get("package_id") != "ZT-SCH-001" or record.get("schedule_id") != policy["metadata"]["schedule_id"]: errors.append("candidate package/schedule mismatch")
    if record.get("schedule_fingerprint") != schedule_fingerprint(policy) or status.get("schedule_fingerprint") != schedule_fingerprint(policy): errors.append("schedule fingerprint mismatch")
    if status.get("definition_status") != "MATCHED" or status.get("enabled") is not True: errors.append("scheduler definition is not matched and enabled")
    if not status.get("last_run_time"): errors.append("scheduler has no last run")
    else:
        started = parse_time(str(record.get("started_at"))).astimezone(timezone.utc)
        last_run = parse_time(str(status["last_run_time"])).astimezone(timezone.utc)
        if abs((last_run - started).total_seconds()) > 300: errors.append("scheduler last-run time does not correlate within five minutes")
        first = parse_time(str(registration["first_scheduled_run"]))
        local_started = started.astimezone(first.tzinfo)
        window_status, _, _ = execution_window_status(policy, local_started)
        if window_status != "OPEN": errors.append("execution is outside the bounded scheduled catch-up window")
    if int(status.get("last_task_result", -1)) != int(record.get("exit_code", -2)): errors.append("task result and candidate exit code differ")
    if parse_time(str(status.get("captured_at"))) < parse_time(str(record.get("ended_at"))): errors.append("scheduler status predates candidate completion")
    if record.get("trigger_claim") != "WINDOWS_TASK_SCHEDULER" or record.get("trigger_verification") != "PENDING_SCHEDULER_CORRELATION": errors.append("candidate trigger claim is not pending correlation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--record", action="store_true")
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--scheduler-status", type=Path, default=STATUS)
    parser.add_argument("--approval-reference")
    args = parser.parse_args()
    if not args.record: args.check = True
    try:
        execution_path = args.execution.resolve()
        boundary = (RUNTIME / "executions").resolve()
        if boundary not in execution_path.parents or execution_path.name != "schedule-record.json": raise ValueError("execution must be a schedule record under the ignored runtime boundary")
        record, status, registration, policy = load(execution_path), load(args.scheduler_status), load(REGISTRATION), load(POLICY)
        errors = correlation_errors(record, status, registration, policy)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}"); return 1
    for error in errors: print(f"[FAIL] {error}")
    if errors: return 1
    print(f"[PASS] scheduler correlation candidate is valid for execution_id={record['execution_id']}; no tracked authority changed.")
    if args.check: return 0
    if not args.approval_reference or not args.approval_reference.startswith("USER_APPROVED_ZT_SCH_001_CORRELATION_"):
        print("[FAIL] --record requires a bounded scheduler-correlation approval reference"); return 2
    correlation = {
        "package_id":"ZT-SCH-001", "schedule_id":record["schedule_id"], "execution_id":record["execution_id"],
        "result":"VERIFIED_SCHEDULER_CORRELATION", "correlated_at":iso(utcnow()),
        "source_record_hash":file_hash(execution_path), "scheduler_status_hash":file_hash(args.scheduler_status),
        "schedule_fingerprint":schedule_fingerprint(policy), "approval_reference":args.approval_reference,
        "authoritative_update_performed":False
    }
    write(execution_path.parent / "correlation-record.json", correlation)
    print("[PASS] ignored scheduler correlation record written; verification history remains unchanged.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
