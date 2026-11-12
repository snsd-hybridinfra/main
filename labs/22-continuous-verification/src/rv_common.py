#!/usr/bin/env python3
"""Shared ZT-RV-001 campaign validation, fingerprint, and assessment helpers."""
from __future__ import annotations
import hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; ZT=ROOT/"docs/zero-trust"; RUNTIME=ROOT/".runtime/zero-trust/repeatable-validation"
CAMPAIGN=ZT/"repeatable-validation-campaign.yaml"; POLICY=ZT/"repeatability-acceptance-policy.yaml"; HISTORY=ZT/"verification-history.yaml"
sys.path.insert(0,str(ROOT/"tools/automation")); from automation_common import ACTION_PATH,WORKFLOW_PATH,build_plan,load as load_automation  # noqa:E402

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"));
    if not isinstance(value,dict): raise ValueError(f"{path} must contain an object")
    return value
def write(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def parse_time(value:str)->datetime:
    result=datetime.fromisoformat(value.replace("Z","+00:00"));
    if result.tzinfo is None: raise ValueError("timezone required")
    return result.astimezone(timezone.utc)
def utcnow()->datetime: return datetime.now(timezone.utc)
def iso(value:datetime)->str: return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
def sha(path:Path)->str:
 data=path.read_bytes().replace(b"\r\n",b"\n").replace(b"\r",b"\n")
 return hashlib.sha256(data).hexdigest()
def canonical_hash(value:Any)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def expected_plan(campaign:dict[str,Any])->dict[str,Any]:
    return build_plan(campaign["selection"]["workflow_id"],"EXECUTE_READ_ONLY",load_automation(ACTION_PATH),load_automation(WORKFLOW_PATH))

def validate_configuration(campaign:dict[str,Any]|None=None,policy:dict[str,Any]|None=None)->list[str]:
    c=campaign or load(CAMPAIGN); p=policy or load(POLICY); errors=[]
    if c.get("metadata",{}).get("campaign_id")!="ZT-RV-001" or c.get("metadata",{}).get("package_id")!="ZT-RV-001": errors.append("campaign/package ID mismatch")
    if c.get("selection",{}).get("capability_id")!="ZT-4.1.1" or c.get("selection",{}).get("validator_id")!="ZTCV-VAL-SYS": errors.append("selected candidate differs from CV recommendation")
    if c.get("requirements",{}).get("evidence_continuity_target")!="EC4_REPEATABLE_RUNTIME": errors.append("target continuity must be EC4 only")
    ep=c.get("execution_policy",{})
    for field in ("automatic_schedule","automatic_retry","automatic_remediation","mutation_allowed","history_auto_append"):
        if ep.get(field) is not False: errors.append(f"{field} must be false")
    req=c.get("requirements",{})
    if req.get("minimum_successful_executions")!=3 or req.get("minimum_consecutive_successes")!=3 or req.get("minimum_execution_separation")!="PT24H": errors.append("campaign must require 3/3 successes separated by PT24H")
    scope=c.get("target_scope_definition",{}); expected_scope=canonical_hash(scope)
    if expected_scope!=c.get("fingerprints",{}).get("target_scope_fingerprint"): errors.append("target scope fingerprint mismatch")
    validator=ROOT/"tools/live-validation/validate-systems-live.ps1"
    expected_validator="1.0.0+sha256:"+sha(validator)
    if expected_validator!=c.get("fingerprints",{}).get("validator_version"): errors.append("validator version mismatch")
    plan=expected_plan(c)
    if plan["plan_hash"]!=c.get("fingerprints",{}).get("expected_plan_hash"): errors.append("deterministic plan hash mismatch")
    if p.get("metadata",{}).get("default_decision")!="DENY" or p.get("selection")!={"capability_id":"ZT-4.1.1","validator_id":"ZTCV-VAL-SYS","workflow_id":"ZT-CV-WF-001"}: errors.append("acceptance policy selection/default mismatch")
    if p.get("criteria",{}).get("target_continuity")!="EC4_REPEATABLE_RUNTIME": errors.append("acceptance target must be EC4")
    return errors

def execution_fingerprint(record:dict[str,Any])->str:
    fields=("campaign_id","package_id","capability_id","validator_id","workflow_id","validator_version","action_catalog_version","workflow_catalog_version","policy_version","target_scope_fingerprint","plan_hash","execution_mode","sanitized_evidence_hash","execution_timestamp")
    return canonical_hash({key:record.get(key) for key in fields})

def campaign_records(history:dict[str,Any])->list[dict[str,Any]]:
    return [item for item in history.get("executions",[]) if item.get("campaign_id")=="ZT-RV-001"]

def assess(records:list[dict[str,Any]],campaign:dict[str,Any],assessment_time:datetime)->dict[str,Any]:
    accepted=[]; rejected=[]; reasons=[]; seen_ids=set(); seen_raw=set(); seen_safe=set(); seen_fp=set(); previous=None; intervals=[]; violations=[]; consecutive=0
    f=campaign["fingerprints"]; r=campaign["requirements"]
    for item in sorted(records,key=lambda x:str(x.get("execution_timestamp",""))):
        local=[]; eid=item.get("execution_id"); raw=item.get("raw_evidence_hash"); safe=item.get("sanitized_evidence_hash"); fp=item.get("execution_fingerprint")
        try: timestamp=parse_time(str(item.get("execution_timestamp","")))
        except ValueError: timestamp=assessment_time; local.append("INVALID_TIMESTAMP")
        if timestamp>assessment_time: local.append("FUTURE_TIMESTAMP")
        if timestamp<=assessment_time and (assessment_time-timestamp).total_seconds()>604800: local.append("STALE_EVIDENCE")
        if eid in seen_ids: local.append("DUPLICATE_EXECUTION_ID")
        if raw in seen_raw or safe in seen_safe: local.append("DUPLICATE_EVIDENCE_HASH")
        if fp in seen_fp: local.append("DUPLICATE_FINGERPRINT")
        seen_ids.add(eid); seen_raw.add(raw); seen_safe.add(safe); seen_fp.add(fp)
        if previous is not None:
            interval=int((timestamp-previous).total_seconds()); intervals.append(interval)
            if interval<86400: local.append("INSUFFICIENT_SEPARATION"); violations.append({"execution_id":eid,"seconds":interval})
        if item.get("plan_hash")!=f["expected_plan_hash"]: local.append("PLAN_DRIFT")
        if item.get("validator_version")!=f["validator_version"]: local.append("VALIDATOR_DRIFT")
        if item.get("target_scope_fingerprint")!=f["target_scope_fingerprint"]: local.append("TARGET_SCOPE_DRIFT")
        if item.get("execution_authority") not in r["required_execution_authority"] or item.get("execution_mode") not in r["required_execution_mode"]: local.append("INVALID_EXECUTION_AUTHORITY_OR_MODE")
        if item.get("sanitization_status")!="PASS": local.append("SANITIZATION_FAILURE")
        if item.get("security_boundary",{}).get("status")!="PASS": local.append("SECURITY_BOUNDARY_FAILURE")
        if int(item.get("exit_code",1))!=0 or int(item.get("fail",1))!=0: local.append("MANDATORY_FAILURE")
        if local: rejected.append({"execution_id":eid,"reasons":local}); consecutive=0
        else: accepted.append(item); previous=timestamp; consecutive+=1
    successes=len(accepted)
    result="REPEATABILITY_ACCEPTED" if successes>=3 and consecutive>=3 and not violations else "REPEATABILITY_PROVISIONAL" if successes>=2 else "IN_PROGRESS" if successes else "NOT_STARTED"
    continuity="EC4_REPEATABLE_RUNTIME" if result=="REPEATABILITY_ACCEPTED" else "EC3_ONE_TIME_RUNTIME"
    if rejected: reasons.extend(sorted({reason for item in rejected for reason in item["reasons"]}))
    return {"campaign_id":"ZT-RV-001","assessment_time":iso(assessment_time),"capability_id":"ZT-4.1.1","validator_id":"ZTCV-VAL-SYS","target_continuity":"EC4_REPEATABLE_RUNTIME","current_continuity":continuity,"execution_history":{"total":len(records),"accepted":successes,"rejected":len(rejected),"successful":successes,"failed":sum(int(x.get("fail",0))>0 for x in records),"consecutive_successes":consecutive,"consecutive_failures":0 if not rejected else 1},"separation":{"required":"PT24H","actual_intervals_seconds":intervals,"violations":violations},"consistency":{"plan_hash":"MATCHED" if not any("PLAN_DRIFT" in x["reasons"] for x in rejected) else "DRIFT","validator_version":"MATCHED" if not any("VALIDATOR_DRIFT" in x["reasons"] for x in rejected) else "DRIFT","target_scope":"MATCHED" if not any("TARGET_SCOPE_DRIFT" in x["reasons"] for x in rejected) else "DRIFT","evidence_schema":"1.0.0"},"freshness":{"status":"STALE" if any("STALE_EVIDENCE" in x["reasons"] for x in rejected) else "FRESH" if records else "NOT_APPLICABLE","maximum_age":"P7D"},"security_boundary":{"status":"PASS" if accepted else "NOT_ASSESSED"},"sanitization":{"status":"PASS" if accepted else "NOT_ASSESSED"},"regressions":{"blocking":len(rejected),"findings":rejected},"acceptance":{"result":result,"confidence":"HIGH" if result=="REPEATABILITY_ACCEPTED" else "MEDIUM" if successes else "LOW","blocking_reasons":reasons,"limitations":["No EC5, EC6, EC7, schedule, or maturity assignment."]},"proposed_updates":["HUMAN_REVIEW_ONLY"],"next_action":"Proceed to P1-ACC-001" if result=="REPEATABILITY_ACCEPTED" else "Run the next independent execution after the enforced 24-hour separation."}
