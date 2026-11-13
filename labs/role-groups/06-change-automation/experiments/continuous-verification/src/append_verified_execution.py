#!/usr/bin/env python3
"""Validate an RV candidate and explicitly append only to verification history."""
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
from rv_common import CAMPAIGN,HISTORY,ROOT,assess,execution_fingerprint,load,parse_time,sha,utcnow,validate_configuration

def validate_candidate(path:Path)->tuple[dict,list[str]]:
 c=load(CAMPAIGN); r=load(path); errors=validate_configuration(c)
 required={"campaign_id","execution_id","execution_timestamp","execution_authority","execution_mode","capability_id","package_id","validator_id","workflow_id","validator_version","plan_hash","target_scope_fingerprint","raw_evidence_reference","sanitized_evidence_reference","raw_evidence_hash","sanitized_evidence_hash","sanitization_status","pass","warn","fail","exit_code","security_boundary","execution_fingerprint"}
 if not required<=set(r): errors.append("candidate required fields missing")
 if r.get("campaign_id")!="ZT-RV-001" or r.get("execution_mode")!="EXECUTE_READ_ONLY" or r.get("execution_authority")!="CODEX_EXECUTED_LIVE_RUNTIME": errors.append("invalid campaign authority or mode")
 if parse_time(str(r.get("execution_timestamp")))>utcnow(): errors.append("future timestamp")
 f=c["fingerprints"]
 for field,expected in (("plan_hash",f["expected_plan_hash"]),("validator_version",f["validator_version"]),("target_scope_fingerprint",f["target_scope_fingerprint"])):
  if r.get(field)!=expected: errors.append(f"{field} mismatch")
 for field,hash_field in (("raw_evidence_reference","raw_evidence_hash"),("sanitized_evidence_reference","sanitized_evidence_hash")):
  target=ROOT/str(r.get(field,""));
  if not target.is_file() or sha(target)!=r.get(hash_field): errors.append(f"{field} missing or hash mismatch")
 if r.get("execution_fingerprint")!=execution_fingerprint(r): errors.append("execution fingerprint mismatch")
 if r.get("sanitization_status")!="PASS" or r.get("security_boundary",{}).get("status")!="PASS" or r.get("exit_code")!=0 or r.get("fail")!=0: errors.append("mandatory execution result failed")
 h=load(HISTORY); ids={x.get("execution_id") for x in h.get("executions",[])}; hashes={v for x in h.get("executions",[]) for v in x.get("evidence_hashes",{}).values()}; fingerprints={x.get("execution_fingerprint") for x in h.get("executions",[])}
 if r.get("execution_id") in ids: errors.append("duplicate execution ID")
 if r.get("sanitized_evidence_hash") in hashes or r.get("raw_evidence_hash") in hashes: errors.append("duplicate evidence hash")
 if r.get("execution_fingerprint") in fingerprints: errors.append("duplicate execution fingerprint")
 prior=[x for x in h.get("executions",[]) if x.get("campaign_id")=="ZT-RV-001"]
 if prior and (parse_time(r["execution_timestamp"])-max(parse_time(x["execution_timestamp"]) for x in prior)).total_seconds()<86400: errors.append("minimum execution separation not satisfied")
 return r,errors

def history_record(r:dict,approval:str)->dict:
 return {**r,"capability_ids":[r["capability_id"]],"execution_scope":"ZT_SYS_001_SEVEN_SYSTEMS_FIXED_VALIDATORS","execution_date":r["execution_timestamp"],"result":"WARN" if r["warn"] else "PASS","evidence_files":[r["sanitized_evidence_reference"]],"evidence_hashes":{r["sanitized_evidence_reference"]:r["sanitized_evidence_hash"]},"freshness_policy_id":"ZTCV-FRESH-LIVE","freshness_status":"FRESH","scheduled_trigger":False,"approval_reference":approval}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__); modes=p.add_mutually_exclusive_group(); modes.add_argument("--check",action="store_true"); modes.add_argument("--append",action="store_true"); p.add_argument("--candidate",type=Path,required=True); p.add_argument("--approval-reference"); p.add_argument("--verbose",action="store_true"); a=p.parse_args();
 if not a.append: a.check=True
 try:r,errors=validate_candidate(a.candidate)
 except (OSError,ValueError,json.JSONDecodeError) as exc: print(f"[FAIL] {exc}"); return 1
 for item in errors: print(f"[FAIL] {item}")
 print(f"Proposed diff: append execution_id={r.get('execution_id')} to {HISTORY}; no other authority file may change.")
 if errors:return 1
 if a.check: print("[PASS] candidate is eligible for explicit review; history is unchanged."); return 0
 if not a.approval_reference: print("[FAIL] --append requires --approval-reference"); return 2
 history=load(HISTORY); history["executions"].append(history_record(r,a.approval_reference)); temporary=HISTORY.with_suffix(".tmp"); temporary.write_text(json.dumps(history,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); os.replace(temporary,HISTORY); print("[PASS] verified execution appended only to verification history."); return 0
if __name__=="__main__": raise SystemExit(main())
