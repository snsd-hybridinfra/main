#!/usr/bin/env python3
"""Run only registered ZT-AUTO-001 handlers with locks, timeouts, and sanitization."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_common import ACTION_PATH, ROOT, WORKFLOW_PATH, build_plan, load, policy_decision

RUNTIME = ROOT / ".runtime/zero-trust/automation"
LOCKS = RUNTIME / "locks"
EXECUTIONS = RUNTIME / "executions"
PROPOSALS = RUNTIME / "proposals"
SAFE_ENV_NAMES = {
    "ALLUSERSPROFILE", "APPDATA", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)",
    "COMMONPROGRAMW6432", "COMSPEC", "COMPUTERNAME", "DRIVERDATA", "HOMEDRIVE",
    "HOMEPATH", "LOCALAPPDATA", "LOGONSERVER", "NUMBER_OF_PROCESSORS", "OS", "PATH", "PATHEXT",
    "PROCESSOR_ARCHITECTURE", "PROCESSOR_IDENTIFIER", "PROCESSOR_LEVEL",
    "PROCESSOR_REVISION", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
    "PROGRAMW6432", "PSMODULEPATH", "PUBLIC", "SESSIONNAME", "SSH_AUTH_SOCK",
    "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "USERDOMAIN",
    "USERDOMAIN_ROAMINGPROFILE", "USERNAME", "USERPROFILE", "WINDIR",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sanitized(text: str) -> str:
    value = text.replace(str(ROOT), "<REPOSITORY_ROOT>").replace(str(Path.home()), "<USER_HOME>")
    value = re.sub(r"(?i)(password|token|secret|authorization)\s*[:=]\s*\S+", r"\1=[REDACTED]", value)
    value = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", value, flags=re.S)
    return value


def command_registry() -> dict[str, list[str]]:
    powershell = shutil.which("powershell") or "powershell"
    return {
        "validate_zero_trust": [sys.executable, str(ROOT / "tools/validate_zero_trust.py"), "--verbose"],
        "check_zero_trust_sync": [sys.executable, str(ROOT / "tools/check_zero_trust_sync.py")],
        "validate_system_inventory": [sys.executable, str(ROOT / "tools/system/validate_system_inventory.py"), "--verbose"],
        "check_system_drift": [sys.executable, str(ROOT / "tools/system/check_configuration_drift.py"), "--verbose"],
        "validate_service_state": [sys.executable, str(ROOT / "tools/system/validate_service_state.py"), "--verbose"],
        "validate_systems_live": [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools/live-validation/validate-systems-live.ps1"), "-OutputDirectory", ".runtime/zero-trust/system/automation-live"],
        "validate_telemetry_sources": [sys.executable, str(ROOT / "tools/telemetry/validate_telemetry_sources.py")],
        "validate_cv_configuration": [sys.executable, str(ROOT / "tools/continuous_verification/validate_verification_configuration.py"), "--verbose"],
        "evaluate_evidence_freshness": [sys.executable, str(ROOT / "tools/continuous_verification/evaluate_evidence_freshness.py"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/freshness.json"), "--verbose"],
        "assess_repeatability": [sys.executable, str(ROOT / "tools/continuous_verification/assess_repeatability.py"), "--freshness", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/freshness.json"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/repeatability.json"), "--verbose"],
        "assess_package_acceptance": [sys.executable, str(ROOT / "tools/continuous_verification/assess_package_acceptance.py"), "--freshness", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/freshness.json"), "--repeatability", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/repeatability.json"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/package-acceptance.json"), "--verbose"],
        "assess_capability_acceptance": [sys.executable, str(ROOT / "tools/continuous_verification/assess_capability_acceptance.py"), "--freshness", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/freshness.json"), "--repeatability", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/repeatability.json"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/capability-acceptance.json")],
        "detect_regressions": [sys.executable, str(ROOT / "tools/continuous_verification/detect_regressions.py"), "--freshness", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/freshness.json"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/regressions.json"), "--verbose"],
        "reassess_maturity": [sys.executable, str(ROOT / "tools/continuous_verification/reassess_maturity.py"), "--check", "--capability-results", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/capability-acceptance.json"), "--output", str(ROOT / ".runtime/zero-trust/continuous-verification/orchestrated/maturity-reassessment.json")],
    }


def condition_allows(condition: str, dependencies: list[str], results: dict[str, dict[str, Any]]) -> bool:
    outcomes = [results.get(item, {}).get("outcome") for item in dependencies]
    if condition == "ALWAYS": return True
    if condition in {"PREVIOUS_PASS", "ALL_DEPENDENCIES_PASS"}: return bool(outcomes) and all(item == "PASS" for item in outcomes)
    if condition == "PREVIOUS_PASS_OR_WARN": return bool(outcomes) and all(item in {"PASS", "WARN"} for item in outcomes)
    if condition in {"PREVIOUS_FAIL", "ANY_DEPENDENCY_FAIL"}: return any(item == "FAIL" for item in outcomes)
    return False


def write_internal(handler: str, execution_root: Path, execution_id: str, results: dict[str, dict[str, Any]]) -> tuple[int, str, str]:
    target_root = execution_root if handler == "write_automation_summary" else PROPOSALS
    target_root.mkdir(parents=True, exist_ok=True)
    names = {
        "write_automation_summary": "automation-summary.json",
        "write_gap_proposal": f"{execution_id}-gap-proposal.json",
        "write_correlation_review": f"{execution_id}-correlation-review.json",
        "write_incident_review": f"{execution_id}-incident-review.json",
    }
    payload = {
        "artifact_type": handler.upper(), "execution_id": execution_id,
        "review_status": "HUMAN_REVIEW_REQUIRED" if handler != "write_automation_summary" else "SANITIZED_RUNTIME_SUMMARY",
        "authoritative_update_performed": False, "external_transmission": False,
        "confirmed_incident": False, "response_action_performed": False,
        "step_outcomes": {key: value.get("outcome") for key, value in results.items()},
    }
    path = target_root / names[handler]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0, f"[PASS] Generated bounded artifact: {path.name}", ""


def acquire_lock(workflow_id: str, execution_id: str) -> tuple[int, Path]:
    LOCKS.mkdir(parents=True, exist_ok=True)
    path = LOCKS / f"{workflow_id}.lock"
    if path.exists():
        age = time.time() - path.stat().st_mtime
        kind = "STALE_LOCK_DETECTED" if age > 1800 else "DUPLICATE_EXECUTION_BLOCKED"
        raise RuntimeError(f"{kind}: {path.name}; no silent deletion performed")
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(descriptor, json.dumps({"execution_id": execution_id, "workflow_id": workflow_id, "created_at": utcnow(), "process_id": os.getpid()}).encode("utf-8"))
    return descriptor, path


def execute(args: argparse.Namespace) -> int:
    mode = "CHECK" if args.check else "PLAN" if args.plan else "EXECUTE_READ_ONLY" if args.execute_read_only else "PROPOSAL_ONLY"
    actions, workflows = load(ACTION_PATH), load(WORKFLOW_PATH)
    plan = build_plan(args.workflow, mode, actions, workflows)
    decision, reasons = policy_decision(plan, mode, load(args.approval) if args.approval else None)
    if not decision.startswith("ALLOW_"):
        print(f"[WARN] {decision}: {'; '.join(reasons)}")
        return 2
    execution_id = f"ZTA-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    execution_root = EXECUTIONS / execution_id
    execution_root.mkdir(parents=True, exist_ok=False)
    (execution_root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    start = time.monotonic(); started = utcnow()
    results: dict[str, dict[str, Any]] = {}
    telemetry: list[dict[str, Any]] = [{"event_type":"WORKFLOW_PLANNED","workflow_id":args.workflow,"outcome":"PASS"}]
    lock_path: Path | None = None; lock_descriptor: int | None = None
    first_exit = 0
    try:
        if mode in {"EXECUTE_READ_ONLY", "PROPOSAL_ONLY"}:
            lock_descriptor, lock_path = acquire_lock(args.workflow, execution_id)
        for step in plan["steps"]:
            step_id = step["step_id"]
            if mode in {"CHECK", "PLAN"}:
                results[step_id] = {"outcome":"SKIPPED","reason":f"{mode}_PERFORMS_NO_ACTION","exit_code":None}
                continue
            if not condition_allows(step["condition"], step["depends_on"], results):
                results[step_id] = {"outcome":"SKIPPED","reason":"CONDITION_NOT_MET","exit_code":None}
                telemetry.append({"event_type":"ACTION_SKIPPED","step_id":step_id,"outcome":"SKIPPED"})
                continue
            handler = step["handler_id"]
            telemetry.append({"event_type":"ACTION_STARTED","step_id":step_id,"outcome":"UNKNOWN"})
            step_start = time.monotonic()
            try:
                if handler in {"write_automation_summary", "write_gap_proposal", "write_correlation_review", "write_incident_review"}:
                    child_exit, stdout, stderr = write_internal(handler, execution_root, execution_id, results)
                else:
                    command = command_registry().get(handler)
                    if command is None: raise RuntimeError("Handler is not in the fixed command registry")
                    environment = {name: value for name, value in os.environ.items() if name in SAFE_ENV_NAMES}
                    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=step["timeout_seconds"], check=False, shell=False, env=environment)
                    child_exit, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
                safe_out, safe_err = sanitized(stdout), sanitized(stderr)
                (execution_root / f"{step_id}.stdout.sanitized.txt").write_text(safe_out, encoding="utf-8")
                (execution_root / f"{step_id}.stderr.sanitized.txt").write_text(safe_err, encoding="utf-8")
                outcome = "FAIL" if child_exit else "WARN" if "[WARN]" in safe_out or "[WARN]" in safe_err else "PASS"
                results[step_id] = {"outcome":outcome,"exit_code":child_exit,"duration_seconds":round(time.monotonic()-step_start,3),"stdout":f"{step_id}.stdout.sanitized.txt","stderr":f"{step_id}.stderr.sanitized.txt"}
                if child_exit and first_exit == 0: first_exit = child_exit
            except subprocess.TimeoutExpired:
                results[step_id] = {"outcome":"TIMED_OUT","exit_code":124,"duration_seconds":round(time.monotonic()-step_start,3)}
                if first_exit == 0: first_exit = 124
            telemetry.append({"event_type":"ACTION_COMPLETED" if results[step_id]["outcome"] in {"PASS","WARN"} else "ACTION_FAILED","step_id":step_id,"outcome":results[step_id]["outcome"]})
    except RuntimeError as exc:
        print(f"[FAIL] {exc}"); first_exit = 2
    finally:
        if lock_descriptor is not None: os.close(lock_descriptor)
        if lock_path is not None and lock_path.exists(): lock_path.unlink()
    outcomes = [item["outcome"] for item in results.values()]
    result = "FAILED" if any(item in {"FAIL","TIMED_OUT","EXECUTION_ERROR"} for item in outcomes) else "PARTIAL" if "WARN" in outcomes else "COMPLETE"
    if mode in {"CHECK","PLAN"}: result = "COMPLETE"
    authority = "CODEX_EXECUTED_LIVE_RUNTIME" if mode == "EXECUTE_READ_ONLY" and any(item["risk_level"] == "R3_REMOTE_READ_ONLY" for item in plan["steps"]) else "CODEX_EXECUTED_LOCAL" if mode == "PROPOSAL_ONLY" else f"{mode}_ONLY"
    telemetry.append({"event_type":f"WORKFLOW_{result}","workflow_id":args.workflow,"outcome":"PASS" if result=="COMPLETE" else "WARN" if result=="PARTIAL" else "FAIL"})
    record = {"execution_id":execution_id,"workflow_id":args.workflow,"execution_mode":mode,"plan_hash":plan["plan_hash"],"execution_authority":authority,"start_time":started,"end_time":utcnow(),"duration_seconds":round(time.monotonic()-start,3),"result":result,"steps":[{"step_id":key,**value} for key,value in results.items()],"sanitization":{"status":"APPLIED","secret_values":0,"raw_command_output_committed":False,"authoritative_update_performed":False},"telemetry_events":telemetry}
    (execution_root / "execution-record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"[{'PASS' if result == 'COMPLETE' else 'WARN' if result == 'PARTIAL' else 'FAIL'}] workflow={args.workflow} mode={mode} result={result} execution_id={execution_id} plan_hash={plan['plan_hash']}")
    if args.verbose:
        for key, value in results.items(): print(f"[{value['outcome']}] {key} exit_code={value.get('exit_code')}")
    return first_exit if first_exit else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--execute-read-only", action="store_true")
    modes.add_argument("--proposal-only", action="store_true")
    parser.add_argument("--workflow", default="ZTA-WF-VAL-001")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if not any((args.check,args.plan,args.execute_read_only,args.proposal_only)): args.check = True
    try: return execute(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}"); return 1


if __name__ == "__main__": raise SystemExit(main())
