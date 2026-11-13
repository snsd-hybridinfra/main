"""Local regression tests for the prepared bounded ZT-SCH-001 schedule."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCH = ROOT / "tools/continuous_verification"
sys.path.insert(0, str(SCH))
from sch_common import POLICY, assess, canonical_hash, execution_window_status, expected_due_dates, load, schedule_fingerprint, validate_configuration  # noqa: E402
from run_scheduled_validation import acquire_lock  # noqa: E402


class ZtSch001Tests(unittest.TestCase):
    def setUp(self): self.policy = load(POLICY)

    def registration(self):
        return {"first_scheduled_run":"2026-08-03T09:00:00+09:00"}

    def record(self, day: int, result: str = "PASS", verified: bool = True):
        started = datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc) + timedelta(days=day)
        return {"execution_id":f"TEST-{day}","started_at":started.isoformat(),"scheduled_date_local":(started+timedelta(hours=9)).date().isoformat(),"result":result,"exit_code":0 if result=="PASS" else 1,"sanitization_status":"PASS","trigger_verification":"VERIFIED_SCHEDULER_CORRELATION" if verified else "PENDING_SCHEDULER_CORRELATION"}

    def test_configuration_is_bounded(self): self.assertEqual([], validate_configuration(self.policy))
    def test_schedule_is_disabled_and_deferred(self):
        package = load(ROOT / "docs/zero-trust/packages/zt-sch-001-package.yaml")
        deferral = load(ROOT / "docs/evidence/zero-trust/zt-sch-001-deferral.sanitized.json")
        self.assertEqual("FINAL_PROJECT_TASK", package["phase"])
        self.assertEqual("DEFERRED_FINAL", package["planning_status"])
        self.assertFalse(package["schedule_enabled"])
        self.assertFalse(package["automated_execution"])
        self.assertEqual("PASS_DISABLED_PRESERVED", deferral["result"])
        self.assertFalse(deferral["enabled"])
        self.assertFalse(deferral["task_deleted"])
        self.assertTrue(deferral["runtime_evidence_preserved"])
    def test_fingerprint_is_deterministic(self): self.assertEqual(schedule_fingerprint(self.policy), schedule_fingerprint(json.loads(json.dumps(self.policy))))
    def test_canonical_hash_ignores_key_order(self): self.assertEqual(canonical_hash({"a":1,"b":2}), canonical_hash({"b":2,"a":1}))
    def test_runtime_loader_accepts_powershell_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"receipt.json"; path.write_bytes(b"\xef\xbb\xbf{\"state\":\"READY\"}\n")
            self.assertEqual("READY",load(path)["state"])
    def test_daily_trigger_has_bounded_catch_up(self): self.assertTrue(self.policy["trigger"]["start_when_available"]); self.assertTrue(self.policy["trigger"]["catch_up"]); self.assertEqual("PT2H",self.policy["trigger"]["catch_up_window"])
    def test_execution_window_is_bounded(self):
        before=datetime(2026,8,3,8,59,tzinfo=timezone(timedelta(hours=9)))
        during=datetime(2026,8,3,10,30,tzinfo=timezone(timedelta(hours=9)))
        after=datetime(2026,8,3,11,1,tzinfo=timezone(timedelta(hours=9)))
        self.assertEqual("BEFORE_DAILY_WINDOW",execution_window_status(self.policy,before)[0])
        self.assertEqual("OPEN",execution_window_status(self.policy,during)[0])
        self.assertEqual("CATCH_UP_WINDOW_EXPIRED",execution_window_status(self.policy,after)[0])
    def test_no_retry_or_remediation(self): self.assertFalse(self.policy["runtime_controls"]["automatic_retry"]); self.assertFalse(self.policy["runtime_controls"]["automatic_remediation"])
    def test_no_infrastructure_or_repository_mutation(self): self.assertFalse(self.policy["runtime_controls"]["infrastructure_mutation"]); self.assertFalse(self.policy["runtime_controls"]["repository_mutation"])
    def test_no_automatic_authority_updates(self): self.assertFalse(self.policy["runtime_controls"]["history_auto_append"]); self.assertFalse(self.policy["runtime_controls"]["maturity_auto_update"]); self.assertFalse(self.policy["runtime_controls"]["phase_auto_completion"])
    def test_due_dates_honor_two_hour_grace(self):
        before=datetime(2026,8,3,1,0,tzinfo=timezone.utc); after=datetime(2026,8,3,2,0,tzinfo=timezone.utc)
        self.assertEqual([], expected_due_dates(self.registration(),self.policy,before)); self.assertEqual(["2026-08-03"],expected_due_dates(self.registration(),self.policy,after))
    def test_three_successful_dates_are_ec5_candidate(self):
        result=assess([self.record(0),self.record(1),self.record(2)],self.registration(),self.policy,datetime(2026,8,6,tzinfo=timezone.utc))
        self.assertEqual("EC5_SCHEDULED_RUNTIME",result["current_continuity"]); self.assertEqual("ELIGIBLE_FOR_EXPLICIT_REVIEW",result["acceptance_candidate"])
    def test_uncorrelated_successes_cannot_reach_ec5(self):
        result=assess([self.record(0,verified=False),self.record(1,verified=False),self.record(2,verified=False)],self.registration(),self.policy,datetime(2026,8,6,tzinfo=timezone.utc))
        self.assertEqual("EC4_REPEATABLE_RUNTIME",result["current_continuity"]); self.assertEqual("ELIGIBLE_FOR_CORRELATION_REVIEW",result["acceptance_candidate"])
    def test_failure_blocks_ec5_candidate(self):
        result=assess([self.record(0),self.record(1,"FAIL"),self.record(2)],self.registration(),self.policy,datetime(2026,8,6,tzinfo=timezone.utc))
        self.assertEqual("EC4_REPEATABLE_RUNTIME",result["current_continuity"]); self.assertIn("TEST-1",result["failed_execution_ids"])
    def test_missed_date_is_detected(self):
        result=assess([self.record(0),self.record(2)],self.registration(),self.policy,datetime(2026,8,6,tzinfo=timezone.utc))
        self.assertIn("2026-08-04",result["missed_scheduled_dates"]); self.assertEqual("NOT_ELIGIBLE",result["acceptance_candidate"])
    def test_three_recent_successes_recover_after_historical_miss(self):
        records=[self.record(0),self.record(2),self.record(3),self.record(4),self.record(5)]
        result=assess(records,self.registration(),self.policy,datetime(2026,8,9,tzinfo=timezone.utc))
        self.assertIn("2026-08-04",result["missed_scheduled_dates"])
        self.assertEqual(["2026-08-06","2026-08-07","2026-08-08"],result["acceptance_window_dates"])
        self.assertEqual("EC5_SCHEDULED_RUNTIME",result["current_continuity"])
    def test_lock_rejects_overlap_without_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"schedule.lock"; descriptor=acquire_lock(path,datetime.now(timezone.utc))
            try:
                with self.assertRaises(RuntimeError): acquire_lock(path,datetime.now(timezone.utc))
                self.assertTrue(path.is_file())
            finally:
                import os
                os.close(descriptor)
    def test_runtime_is_ignored(self):
        result=subprocess.run(["git","check-ignore",".runtime/zero-trust/scheduled-validation/test"],cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(0,result.returncode)
    def test_management_requires_explicit_install_approval(self):
        text=(ROOT/"tools/live-validation/manage-scheduled-validation.ps1").read_text(encoding="utf-8")
        self.assertIn("USER_APPROVED_ZT_SCH_001_${Operation}",text); self.assertIn("'Update'",text); self.assertIn("LogonType Interactive",text); self.assertIn("RunLevel Limited",text)
    def test_schedule_wrapper_cannot_install_task(self):
        text=(ROOT/"tools/live-validation/run-scheduled-validation.ps1").read_text(encoding="utf-8")
        self.assertNotIn("Register-ScheduledTask",text); self.assertNotIn("Unregister-ScheduledTask",text)
    def test_scheduled_claim_requires_execute_mode(self):
        result=subprocess.run([sys.executable,str(SCH/"run_repeatability_campaign.py"),"--check","--scheduled-trigger"],cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(2,result.returncode); self.assertIn("requires --execute-read-only",result.stdout)


if __name__ == "__main__": unittest.main()
