"""Regression tests for bounded ZT-CV-001 decisions."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CV = ROOT / "tools/continuous_verification"
sys.path.insert(0, str(CV))
from cv_common import (  # noqa: E402
    PATHS, capability_acceptance_results, execution_success, freshness_results,
    load, maturity_results, package_acceptance_results, parse_duration,
    parse_time, regression_results, repeatability_results, sha256_file,
)
from validate_verification_configuration import validate  # noqa: E402


class ZtCv001Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 1, 23, 5, tzinfo=timezone.utc)
        self.history = load(PATHS["history"])
        self.freshness_policy = load(PATHS["freshness"])

    def fresh(self, history=None): return freshness_results(history or self.history, self.freshness_policy, self.now)
    def repeat(self, history=None):
        selected = history or self.history
        return repeatability_results(selected, self.fresh(selected))
    def record(self, index=1): return copy.deepcopy(self.history["executions"][index])

    def test_configuration_valid(self): self.assertEqual([], validate()[0])
    def test_duration_days(self): self.assertEqual(7, parse_duration("P7D").days)
    def test_duration_hours(self): self.assertEqual(24, parse_duration("PT24H").total_seconds()/3600)
    def test_duration_malformed(self): self.assertRaises(ValueError, parse_duration, "DAILY")
    def test_timezone_required(self): self.assertRaises(ValueError, parse_time, "2026-07-22T00:00:00")
    def test_current_history_retains_truthful_freshness_counts(self):
        states=[x["freshness_status"] for x in self.fresh()]
        self.assertEqual({"FRESH":7,"AGING":0,"STALE":10},{state:states.count(state) for state in {"FRESH","AGING","STALE"}})
    def test_future_timestamp_unknown(self):
        h={"executions":[self.record()]}; h["executions"][0]["execution_date"]="2099-01-01T00:00:00Z"; self.assertEqual("UNKNOWN",self.fresh(h)[0]["freshness_status"])
    def test_aging_classification(self):
        h={"executions":[self.record()]}; h["executions"][0]["execution_date"]="2026-07-23T00:00:00Z"; self.assertEqual("AGING",self.fresh(h)[0]["freshness_status"])
    def test_stale_classification(self):
        h={"executions":[self.record()]}; h["executions"][0]["execution_date"]="2026-07-10T00:00:00Z"; self.assertEqual("STALE",self.fresh(h)[0]["freshness_status"])
    def test_expired_classification(self):
        h={"executions":[self.record()]}; h["executions"][0]["execution_date"]="2026-06-01T00:00:00Z"; self.assertEqual("EXPIRED",self.fresh(h)[0]["freshness_status"])
    def test_pass_is_success(self): self.assertTrue(execution_success(self.record()))
    def test_warn_without_failure_is_success(self): self.assertTrue(execution_success(self.record(1)))
    def test_failure_is_not_success(self):
        r=self.record(); r["fail"]=1; self.assertFalse(execution_success(r))
    def test_unsanitized_is_not_success(self):
        r=self.record(); r["sanitization_status"]="FAIL"; self.assertFalse(execution_success(r))
    def test_current_history_has_one_bounded_ec4_group(self):
        states=[x["evidence_continuity"] for x in self.repeat()]; self.assertEqual(1,states.count("EC4_REPEATABLE_RUNTIME")); self.assertEqual(12,states.count("EC3_ONE_TIME_RUNTIME"))
    def test_one_run_never_ec4(self): self.assertEqual("EC3_ONE_TIME_RUNTIME",self.repeat({"executions":[self.record()]})[0]["evidence_continuity"])
    def test_three_unrecorded_plan_hashes_not_ec4(self):
        base=self.record(); records=[]
        for n in range(3):
            r=copy.deepcopy(base); r["execution_id"]=f"T{n}"; r["execution_date"]=(self.now-timedelta(hours=24*n)).isoformat(); records.append(r)
        self.assertEqual("EC3_ONE_TIME_RUNTIME",self.repeat({"executions":records})[0]["evidence_continuity"])
    def test_three_stable_independent_runs_reach_ec4(self):
        base=self.record(); records=[]
        for n in range(3):
            r=copy.deepcopy(base); r["execution_id"]=f"T{n}"; r["plan_hash"]="a"*64; r["execution_date"]=(self.now-timedelta(hours=24*n)).isoformat(); records.append(r)
        self.assertEqual("EC4_REPEATABLE_RUNTIME",self.repeat({"executions":records})[0]["evidence_continuity"])
    def test_duplicate_ids_block_independence(self):
        base=self.record(); base["plan_hash"]="a"*64; records=[copy.deepcopy(base) for _ in range(3)]
        self.assertNotEqual("EC4_REPEATABLE_RUNTIME",self.repeat({"executions":records})[0]["evidence_continuity"])
    def test_manual_runs_never_ec5(self):
        base=self.record(); records=[]
        for n in range(3):
            r=copy.deepcopy(base); r["execution_id"]=f"T{n}"; r["plan_hash"]="a"*64; r["execution_date"]=(self.now-timedelta(days=n)).isoformat(); r["scheduled_trigger"]=False; records.append(r)
        self.assertEqual("EC4_REPEATABLE_RUNTIME",self.repeat({"executions":records})[0]["evidence_continuity"])
    def test_three_distinct_scheduled_dates_reach_ec5(self):
        base=self.record(); records=[]
        for n in range(3):
            r=copy.deepcopy(base); r["execution_id"]=f"T{n}"; r["plan_hash"]="a"*64; r["execution_date"]=(self.now-timedelta(days=n)).isoformat(); r["scheduled_trigger"]=True; records.append(r)
        self.assertEqual("EC5_SCHEDULED_RUNTIME",self.repeat({"executions":records})[0]["evidence_continuity"])
    def test_package_gate_count(self): self.assertEqual(10,len(load(PATHS["gates"])["gates"]))
    def test_capability_acceptance_count(self): self.assertEqual(12,len(load(PATHS["capabilities"])["capabilities"]))
    def test_package_results_are_non_authoritative(self):
        r=package_acceptance_results(load(PATHS["gates"]),self.history,self.fresh(),self.repeat()); self.assertTrue(all(x["authoritative_update_performed"] is False for x in r))
    def test_current_fnd_gate_is_accepted(self):
        r=package_acceptance_results(load(PATHS["gates"]),self.history,self.fresh(),self.repeat()); fnd=next(x for x in r if x["package_id"]=="ZT-FND-001"); self.assertEqual("ACCEPTED",fnd["assessment_state"]); self.assertEqual([],fnd["findings"])
    def test_current_cv_gate_is_partially_accepted(self):
        r=package_acceptance_results(load(PATHS["gates"]),self.history,self.fresh(),self.repeat()); cv=next(x for x in r if x["package_id"]=="ZT-CV-001"); self.assertEqual("PARTIALLY_ACCEPTED",cv["assessment_state"])
    def test_capability_results_are_non_authoritative(self):
        r=capability_acceptance_results(load(PATHS["capabilities"]),self.history,self.fresh(),self.repeat()); self.assertTrue(all(x["authoritative_update_performed"] is False for x in r))
    def test_maturity_is_retained(self):
        c=capability_acceptance_results(load(PATHS["capabilities"]),self.history,self.fresh(),self.repeat()); self.assertTrue(all(x["decision"]=="RETAIN" for x in maturity_results(c)))
    def test_no_maturity_upgrade(self):
        c=capability_acceptance_results(load(PATHS["capabilities"]),self.history,self.fresh(),self.repeat()); self.assertTrue(all(x["source_maturity"]==x["candidate_maturity"] for x in maturity_results(c)))
    def test_current_regressions_are_seven_non_rv_freshness_findings(self):
        findings=regression_results(self.history,self.fresh()); self.assertEqual(7,len(findings)); self.assertTrue(all(x["type"]=="EVIDENCE_FRESHNESS_REGRESSION" and not str(x["execution_id"]).startswith("ZTRV-") for x in findings),findings)
    def test_text_evidence_hash_is_checkout_eol_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); lf = root / "lf.yaml"; crlf = root / "crlf.yaml"
            lf.write_bytes(b'{"result":"PASS"}\n'); crlf.write_bytes(b'{"result":"PASS"}\r\n')
            self.assertEqual(sha256_file(lf), sha256_file(crlf))
    def test_hash_change_detected(self):
        h={"executions":[self.record()]}; key=next(iter(h["executions"][0]["evidence_hashes"])); h["executions"][0]["evidence_hashes"][key]="0"*64; self.assertTrue(regression_results(h,self.fresh(h)))
    def test_superseded_stale_record_is_not_a_current_freshness_regression(self):
        old=self.record(); old["execution_date"]="2026-07-01T00:00:00Z"
        current=copy.deepcopy(old); current["execution_id"]="CURRENT"; current["execution_date"]="2026-07-30T04:00:00Z"
        h={"executions":[old,current]}
        findings=regression_results(h,self.fresh(h))
        self.assertFalse(any(item["type"]=="EVIDENCE_FRESHNESS_REGRESSION" for item in findings),findings)
    def test_future_record_is_not_current_at_historical_assessment(self):
        current=self.record(); future=copy.deepcopy(current)
        future["execution_id"]="FUTURE"; future["execution_date"]="2099-01-01T00:00:00Z"
        h={"executions":[current,future]}
        findings=regression_results(h,self.fresh(h))
        self.assertFalse(any(item["execution_id"]=="FUTURE" and item["type"]=="EVIDENCE_FRESHNESS_REGRESSION" for item in findings),findings)
    def test_foundation_wrapper_preserves_known_openstack_degraded_as_warning(self):
        text=(ROOT/"tools/live-validation/run-foundation-validation.ps1").read_text(encoding="utf-8")
        self.assertIn("CURRENT_DEGRADED_46_PASS_0_WARN_4_FAIL",text)
        self.assertIn("automatic_remediation_performed = $false",text)
    def test_fixture_catalog_is_inert(self):
        value=load(ROOT/"tests/fixtures/zt-cv-001/fixture-catalog.yaml"); self.assertEqual("TEST_FIXTURE_ONLY_NON_EXECUTABLE",value["fixture_scope"]); self.assertGreaterEqual(len(value["fixtures"]),18)
    def test_runtime_is_ignored(self):
        result=subprocess.run(["git","check-ignore",".runtime/zero-trust/continuous-verification/test"],cwd=ROOT,capture_output=True,text=True,check=False); self.assertEqual(0,result.returncode)
    def test_wrapper_has_no_schedule_installation(self):
        text=(ROOT/"tools/live-validation/run-continuous-verification.ps1").read_text(encoding="utf-8"); self.assertNotIn("Register-ScheduledTask",text); self.assertNotIn("schtasks /create",text.lower())
    def test_wrapper_has_no_remediation(self):
        text=(ROOT/"tools/live-validation/run-continuous-verification.ps1").read_text(encoding="utf-8"); self.assertNotIn("Restart-Service",text); self.assertNotIn("Remove-Item",text)


if __name__ == "__main__": unittest.main()
