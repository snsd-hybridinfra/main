#!/usr/bin/env python3
"""Check, plan, execute, or assess the bounded ZT-SCH-001 daily schedule."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sch_common import POLICY, REGISTRATION, ROOT, RUNTIME, assess, execution_window_status, file_hash, iso, load, schedule_fingerprint, utcnow, validate_configuration, write

sys.path.insert(0, str(ROOT / "tools/continuous_verification"))
from verify_sanitized_evidence import findings as sanitizer_findings  # noqa: E402


def acquire_lock(path: Path, now: datetime) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError("DUPLICATE_EXECUTION_BLOCKED: active schedule lock exists; no silent deletion performed") from exc
    os.write(descriptor, (json.dumps({"created_at": iso(now), "process_id": os.getpid()}) + "\n").encode("utf-8"))
    return descriptor


def terminate_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None: return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired: process.kill()


def run_child(command: list[str], timeout: int) -> tuple[int, str, bool]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", shell=False, start_new_session=os.name != "nt", creationflags=creationflags)
    try:
        output, _ = process.communicate(timeout=timeout)
        return int(process.returncode or 0), output, False
    except subprocess.TimeoutExpired:
        terminate_tree(process)
        output, _ = process.communicate()
        return 124, output, True


def execution_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted((RUNTIME / "executions").glob("*/schedule-record.json")):
        try:
            record = load(path)
            correlation = path.parent / "correlation-record.json"
            if correlation.is_file():
                reviewed = load(correlation)
                if reviewed.get("result") == "VERIFIED_SCHEDULER_CORRELATION" and reviewed.get("execution_id") == record.get("execution_id") and reviewed.get("source_record_hash") == file_hash(path):
                    record["trigger_verification"] = "VERIFIED_SCHEDULER_CORRELATION"
            records.append(record)
        except (OSError, ValueError, json.JSONDecodeError): continue
    return records


def execute(policy: dict, verbose: bool) -> int:
    now = utcnow()
    local_now = datetime.now().astimezone()
    window_status, scheduled_start, catch_up_deadline = execution_window_status(policy, local_now)
    if window_status != "OPEN":
        print(f"[FAIL] {window_status}: allowed={scheduled_start.isoformat()}..{catch_up_deadline.isoformat()}; no attempt marker was written.")
        return 2
    scheduled_date = local_now.date().isoformat()
    marker = RUNTIME / "attempted-dates" / f"{scheduled_date}.json"
    if marker.exists():
        print(f"[FAIL] ONE_ATTEMPT_PER_LOCAL_DATE: {scheduled_date} already has an attempt; automatic retry remains disabled.")
        return 2
    lock = RUNTIME / "locks/ZT-SCH-001.lock"
    descriptor: int | None = None
    execution_id = f"ZTSCH-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    root = RUNTIME / "executions" / execution_id
    raw = root / "scheduled-run.raw.txt"
    safe = root / "scheduled-run.sanitized.txt"
    root.mkdir(parents=True, exist_ok=False)
    try:
        descriptor = acquire_lock(lock, now)
        command = [sys.executable, str(ROOT / "tools/continuous_verification/run_repeatability_campaign.py"), "--execute-read-only", "--scheduled-trigger"]
        started = time.monotonic()
        exit_code, output, timed_out = run_child(command, int(policy["runtime_controls"]["timeout_seconds"]))
        duration = round(time.monotonic() - started, 3)
        raw.write_text(output, encoding="utf-8")
        sanitizer = [sys.executable, str(ROOT / "tools/live-validation/sanitize-live-evidence.py"), "--input", str(raw), "--output", str(safe)]
        sanitized = subprocess.run(sanitizer, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False, shell=False)
        bad = sanitizer_findings(safe.read_text(encoding="utf-8", errors="replace")) if safe.is_file() else ["SANITIZED_OUTPUT_MISSING"]
        match = re.search(r"execution_id=(ZTRV-[A-Za-z0-9-]+)", output)
        source_id = match.group(1) if match else None
        source = ROOT / ".runtime/zero-trust/repeatable-validation/executions" / str(source_id) / "execution-record.json"
        source_exists = bool(source_id and source.is_file())
        final_exit = 124 if timed_out else exit_code if exit_code else sanitized.returncode if sanitized.returncode else 1 if bad or not source_exists else 0
        result = "PASS" if final_exit == 0 else "TIMEOUT" if timed_out else "FAIL"
        record = {
            "package_id": "ZT-SCH-001", "schedule_id": policy["metadata"]["schedule_id"],
            "execution_id": execution_id, "started_at": iso(now), "ended_at": iso(utcnow()),
            "scheduled_date_local": scheduled_date, "local_utc_offset": local_now.strftime("%z"),
            "execution_window_status": window_status, "scheduled_start_local": scheduled_start.isoformat(),
            "catch_up_deadline_local": catch_up_deadline.isoformat(), "delayed_start": local_now > scheduled_start,
            "trigger_claim": "WINDOWS_TASK_SCHEDULER", "trigger_verification": "PENDING_SCHEDULER_CORRELATION",
            "schedule_fingerprint": schedule_fingerprint(policy), "source_rv_execution_id": source_id,
            "source_rv_record": str(source.relative_to(ROOT)).replace("\\", "/") if source_exists else None,
            "sanitized_evidence_reference": str(safe.relative_to(ROOT)).replace("\\", "/") if safe.is_file() else None,
            "sanitized_evidence_hash": file_hash(safe) if safe.is_file() else None,
            "sanitization_status": "PASS" if not bad and sanitized.returncode == 0 else "FAIL",
            "result": result, "exit_code": final_exit, "duration_seconds": duration,
            "timeout_enforced": timed_out, "exclusive_lock_enforced": True, "one_attempt_per_local_date_enforced": True,
            "automatic_retry_performed": False, "infrastructure_mutation_performed": False,
            "repository_mutation_performed": False, "authoritative_update_performed": False,
            "limitations": ["A bounded delayed start remains a candidate claim until correlated with the registered task status and explicitly reviewed."]
        }
        write(root / "schedule-record.json", record)
        write(marker, {"scheduled_date_local": scheduled_date, "execution_id": execution_id, "result": result})
        print(f"[{'PASS' if result == 'PASS' else 'FAIL'}] execution_id={execution_id} result={result} source_rv_execution_id={source_id or 'NONE'} candidate={root/'schedule-record.json'}")
        if verbose: print(f"[INFO] duration_seconds={duration} sanitizer_findings={len(bad)} timeout={timed_out}")
        return final_exit
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 2
    finally:
        if descriptor is not None: os.close(descriptor)
        if descriptor is not None and lock.exists(): lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--execute-read-only", action="store_true")
    modes.add_argument("--assess", action="store_true")
    parser.add_argument("--assessment-time")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if not any((args.check, args.plan, args.execute_read_only, args.assess)): args.check = True
    try: policy = load(POLICY)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}"); return 1
    errors = validate_configuration(policy)
    for error in errors: print(f"[FAIL] {error}")
    if errors: return 1
    if args.check:
        print(f"[PASS] ZT-SCH-001 configuration is valid; schedule_fingerprint={schedule_fingerprint(policy)}; no scheduler or live validator action performed.")
        return 0
    if args.plan:
        print(json.dumps({"schedule_id":policy["metadata"]["schedule_id"],"task":policy["scheduler"],"trigger":policy["trigger"],"runtime_controls":policy["runtime_controls"],"schedule_fingerprint":schedule_fingerprint(policy)}, indent=2))
        print("[PASS] deterministic schedule plan generated; no scheduler or live validator action performed.")
        return 0
    if args.execute_read_only: return execute(policy, args.verbose)
    now = datetime.fromisoformat(args.assessment_time.replace("Z", "+00:00")) if args.assessment_time else utcnow()
    registration = load(REGISTRATION) if REGISTRATION.is_file() else None
    result = assess(execution_records(), registration, policy, now)
    target = RUNTIME / "assessments/ZT-SCH-001-assessment.json"
    write(target, result)
    print(f"[PASS] installed={result['installed']} executions={result['execution_count']} missed={len(result['missed_scheduled_dates'])} continuity={result['current_continuity']} output={target}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
