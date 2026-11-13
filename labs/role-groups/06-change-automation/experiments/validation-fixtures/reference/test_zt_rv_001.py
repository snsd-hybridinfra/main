"""Regression tests for the manual ZT-RV-001 evidence-continuity campaign."""
from __future__ import annotations
import copy,subprocess,sys,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RV=ROOT/"tools/continuous_verification"; sys.path.insert(0,str(RV))
from rv_common import CAMPAIGN,POLICY,assess,canonical_hash,execution_fingerprint,expected_plan,load,sha,validate_configuration  # noqa:E402
from run_repeatability_campaign import next_execution_not_before,observed_warning_categories  # noqa:E402
from verify_sanitized_evidence import findings  # noqa:E402

class ZtRv001Tests(unittest.TestCase):
 def setUp(self): self.c=load(CAMPAIGN); self.p=load(POLICY); self.now=datetime(2026,7,30,tzinfo=timezone.utc)
 def record(self,n=0):
  t=self.now-timedelta(days=3-n); r={"campaign_id":"ZT-RV-001","package_id":"ZT-RV-001","capability_id":"ZT-4.1.1","validator_id":"ZTCV-VAL-SYS","workflow_id":"ZT-CV-WF-001","validator_version":self.c["fingerprints"]["validator_version"],"action_catalog_version":"1.1.0","workflow_catalog_version":"1.1.0","policy_version":"1.0.0","target_scope_fingerprint":self.c["fingerprints"]["target_scope_fingerprint"],"plan_hash":self.c["fingerprints"]["expected_plan_hash"],"execution_mode":"EXECUTE_READ_ONLY","execution_authority":"CODEX_EXECUTED_LIVE_RUNTIME","execution_id":f"TEST-{n}","execution_timestamp":t.isoformat(),"raw_evidence_hash":f"{n+1:064x}","sanitized_evidence_hash":f"{n+10:064x}","sanitization_status":"PASS","pass":8,"warn":2,"fail":0,"exit_code":0,"security_boundary":{"status":"PASS"}}
  r["execution_fingerprint"]=execution_fingerprint(r); return r
 def result(self,records): return assess(records,self.c,self.now)
 def test_configuration_valid(self): self.assertEqual([],validate_configuration(self.c,self.p))
 def test_candidate_exactly_one(self): self.assertEqual("ZT-4.1.1",self.c["selection"]["capability_id"])
 def test_validator_exactly_one(self): self.assertEqual("ZTCV-VAL-SYS",self.c["selection"]["validator_id"])
 def test_target_ec4_only(self): self.assertEqual("EC4_REPEATABLE_RUNTIME",self.c["requirements"]["evidence_continuity_target"])
 def test_schedule_disabled(self): self.assertFalse(self.c["execution_policy"]["automatic_schedule"])
 def test_remediation_disabled(self): self.assertFalse(self.c["execution_policy"]["automatic_remediation"])
 def test_mutation_disabled(self): self.assertFalse(self.c["execution_policy"]["mutation_allowed"])
 def test_history_auto_append_disabled(self): self.assertFalse(self.c["execution_policy"]["history_auto_append"])
 def test_current_authority_is_accepted_at_ec4(self):
  self.assertEqual("COMPLETED",self.c["acceptance"]["current_state"]); self.assertEqual("REPEATABILITY_ACCEPTED",self.c["acceptance"]["acceptance_decision"]); self.assertEqual(3,self.c["acceptance"]["successful_independent_executions"]); self.assertEqual("EC4_REPEATABLE_RUNTIME",self.c["acceptance"]["current_continuity"])
 def test_plan_hash_stable(self): self.assertEqual(expected_plan(self.c)["plan_hash"],expected_plan(self.c)["plan_hash"])
 def test_plan_hash_matches_campaign(self): self.assertEqual(self.c["fingerprints"]["expected_plan_hash"],expected_plan(self.c)["plan_hash"])
 def test_scope_hash_matches(self): self.assertEqual(self.c["fingerprints"]["target_scope_fingerprint"],canonical_hash(self.c["target_scope_definition"]))
 def test_one_record_remains_ec3(self): self.assertEqual("EC3_ONE_TIME_RUNTIME",self.result([self.record(0)])["current_continuity"])
 def test_two_records_provisional(self): self.assertEqual("REPEATABILITY_PROVISIONAL",self.result([self.record(0),self.record(1)])["acceptance"]["result"])
 def test_three_records_reach_ec4(self): self.assertEqual("EC4_REPEATABLE_RUNTIME",self.result([self.record(0),self.record(1),self.record(2)])["current_continuity"])
 def test_duplicate_id_rejected(self):
  a=self.record(0); b=self.record(1); b["execution_id"]=a["execution_id"]; b["execution_fingerprint"]=execution_fingerprint(b); self.assertGreater(self.result([a,b])["execution_history"]["rejected"],0)
 def test_duplicate_raw_hash_rejected(self):
  a=self.record(0); b=self.record(1); b["raw_evidence_hash"]=a["raw_evidence_hash"]; b["execution_fingerprint"]=execution_fingerprint(b); self.assertGreater(self.result([a,b])["execution_history"]["rejected"],0)
 def test_duplicate_safe_hash_rejected(self):
  a=self.record(0); b=self.record(1); b["sanitized_evidence_hash"]=a["sanitized_evidence_hash"]; b["execution_fingerprint"]=execution_fingerprint(b); self.assertGreater(self.result([a,b])["execution_history"]["rejected"],0)
 def test_duplicate_fingerprint_rejected(self):
  a=self.record(0); b=self.record(1); b["execution_fingerprint"]=a["execution_fingerprint"]; self.assertGreater(self.result([a,b])["execution_history"]["rejected"],0)
 def test_insufficient_separation_rejected(self):
  a=self.record(0); b=self.record(1); b["execution_timestamp"]=(datetime.fromisoformat(a["execution_timestamp"])+timedelta(hours=1)).isoformat(); b["execution_fingerprint"]=execution_fingerprint(b); self.assertTrue(self.result([a,b])["separation"]["violations"])
 def test_next_execution_uses_reviewed_history_only(self):
  accepted=self.record(0); expected=datetime.fromisoformat(accepted["execution_timestamp"])+timedelta(hours=24)
  self.assertEqual(expected,next_execution_not_before(self.c,{"executions":[accepted]}))
 def test_future_timestamp_rejected(self):
  a=self.record(); a["execution_timestamp"]=(self.now+timedelta(days=1)).isoformat(); a["execution_fingerprint"]=execution_fingerprint(a); self.assertGreater(self.result([a])["execution_history"]["rejected"],0)
 def test_plan_drift_rejected(self):
  a=self.record(); a["plan_hash"]="0"*64; a["execution_fingerprint"]=execution_fingerprint(a); self.assertIn("PLAN_DRIFT",self.result([a])["acceptance"]["blocking_reasons"])
 def test_validator_drift_rejected(self):
  a=self.record(); a["validator_version"]="2.0.0"; a["execution_fingerprint"]=execution_fingerprint(a); self.assertIn("VALIDATOR_DRIFT",self.result([a])["acceptance"]["blocking_reasons"])
 def test_scope_drift_rejected(self):
  a=self.record(); a["target_scope_fingerprint"]="0"*64; a["execution_fingerprint"]=execution_fingerprint(a); self.assertIn("TARGET_SCOPE_DRIFT",self.result([a])["acceptance"]["blocking_reasons"])
 def test_sanitization_failure_rejected(self):
  a=self.record(); a["sanitization_status"]="FAIL"; self.assertIn("SANITIZATION_FAILURE",self.result([a])["acceptance"]["blocking_reasons"])
 def test_security_failure_rejected(self):
  a=self.record(); a["security_boundary"]["status"]="FAIL"; self.assertIn("SECURITY_BOUNDARY_FAILURE",self.result([a])["acceptance"]["blocking_reasons"])
 def test_mandatory_failure_rejected(self):
  a=self.record(); a["fail"]=1; a["exit_code"]=1; self.assertIn("MANDATORY_FAILURE",self.result([a])["acceptance"]["blocking_reasons"])
 def test_password_pattern_detected(self): self.assertIn("PASSWORD",findings("password=TEST_FIXTURE"))
 def test_private_key_pattern_detected(self): self.assertIn("PRIVATE_KEY",findings("-----BEGIN PRIVATE KEY-----"))
 def test_sanitized_text_passes(self): self.assertEqual([],findings("[PASS] fixed validator completed"))
 def test_evidence_hash_is_checkout_eol_independent(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory); lf=root/"lf.txt"; crlf=root/"crlf.txt"; lf.write_bytes(b"PASS\n"); crlf.write_bytes(b"PASS\r\n")
   self.assertEqual(sha(lf),sha(crlf))
 def test_observed_warning_categories_do_not_copy_unseen_allowlist_values(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory); (root/"validate-live-systems.stdout.sanitized.txt").write_text("[WARN] evidence.vulnerability: has no dedicated scanner evidence.\n[WARN] drift.unassessed: metadata only.\n[WARN] service.degraded: reviewed.\n",encoding="utf-8")
   self.assertEqual(["ENDPOINT_SCANNER_GAP","CONFIGURATION_ONLY_RECORDS","SERVICE_DEGRADED"],observed_warning_categories(root))
 def test_observed_warning_categories_detect_current_openstack_only_when_present(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory); (root/"validate-live-systems.stdout.sanitized.txt").write_text("OPENSTACK CURRENT_DEGRADED\n",encoding="utf-8")
   self.assertEqual(["OPENSTACK_CURRENT_DEGRADED"],observed_warning_categories(root))
 def test_wrapper_has_no_schedule_install(self):
  text=(ROOT/"tools/live-validation/run-repeatable-validation-pilot.ps1").read_text(encoding="utf-8"); self.assertNotIn("Register-ScheduledTask",text); self.assertNotIn("schtasks",text.lower())
 def test_runtime_is_ignored(self):
  result=subprocess.run(["git","check-ignore",".runtime/zero-trust/repeatable-validation/test"],cwd=ROOT,capture_output=True,text=True,check=False); self.assertEqual(0,result.returncode)
 def test_fixture_catalog_inert(self):
  value=load(ROOT/"tests/fixtures/zt-rv-001/fixture-catalog.yaml"); self.assertEqual("TEST_FIXTURE_ONLY_NON_EXECUTABLE",value["fixture_scope"]); self.assertGreaterEqual(len(value["fixtures"]),18)

if __name__=="__main__": unittest.main()
