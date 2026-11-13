#!/usr/bin/env python3
"""Check, plan, execute, or assess the single fixed ZT-RV-001 campaign."""
from __future__ import annotations
import argparse,json,os,re,shutil,subprocess,sys,uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
from rv_common import CAMPAIGN,HISTORY,POLICY,ROOT,RUNTIME,assess,expected_plan,execution_fingerprint,iso,load,parse_time,sha,utcnow,validate_configuration,write,campaign_records
from verify_sanitized_evidence import findings as sanitizer_findings

def next_execution_not_before(campaign:dict,history:dict)->datetime:
 not_before=parse_time(campaign["execution_policy"]["not_before"])
 prior=campaign_records(history)
 if prior:
  not_before=max(not_before,max(parse_time(x["execution_timestamp"]) for x in prior)+timedelta(hours=24))
 return not_before

def verify_security_boundary(campaign:dict)->dict:
 ssh=shutil.which("ssh") or "ssh"; aliases=campaign["target_scope_definition"]["approved_ssh_aliases"]; checks=[]
 for alias in aliases:
  for name,request in (("INTERACTIVE_SHELL_BLOCKED",[]),("ARBITRARY_COMMAND_BLOCKED",["TEST_FIXTURE_HARMLESS_DENIED"]),("PROTECTED_FILE_READ_BLOCKED",["cat","/etc/shadow"])):
   command=[ssh,"-o","BatchMode=yes","-o","ConnectTimeout=10",alias,*request]
   try: child=subprocess.run(command,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=False,shell=False); blocked=child.returncode!=0
   except subprocess.TimeoutExpired: blocked=False
   checks.append({"alias":alias,"check":name,"blocked":blocked})
 return {"status":"PASS" if all(x["blocked"] for x in checks) else "FAIL","batch_mode_allowed_command":"VALIDATED_BY_FIXED_WORKFLOW","negative_checks":checks,"limitations":["Only harmless denied requests were used; no protected content was captured."]}

def observed_warning_categories(execution_root:Path)->list[str]:
 path=execution_root/"validate-live-systems.stdout.sanitized.txt"
 text=path.read_text(encoding="utf-8",errors="replace") if path.is_file() else ""
 observed=[]
 for category,markers in (
  ("OPENSTACK_CURRENT_DEGRADED",("CURRENT_DEGRADED",)),
  ("ENDPOINT_REBOOT_REQUIRED",("reboot is required","reboot required")),
  ("ENDPOINT_SCANNER_GAP",("has no dedicated scanner evidence",)),
  ("CONFIGURATION_ONLY_RECORDS",("drift.unassessed",)),
  ("SERVICE_DEGRADED",("service.degraded",)),
 ):
  if any(marker.lower() in text.lower() for marker in markers): observed.append(category)
 return observed

def execute(campaign:dict,verbose:bool,scheduled_trigger:bool=False)->int:
 now=utcnow(); not_before=next_execution_not_before(campaign,load(HISTORY))
 if now<not_before: print(f"[FAIL] MINIMUM_SEPARATION: next execution not before {iso(not_before)}"); return 2
 lock=RUNTIME/"locks/ZT-RV-001.lock"; lock.parent.mkdir(parents=True,exist_ok=True)
 if lock.exists(): print("[FAIL] campaign lock exists; no silent deletion performed"); return 2
 lock.write_text(json.dumps({"created_at":iso(now),"process_id":os.getpid()})+"\n",encoding="utf-8")
 execution_id=f"ZTRV-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"; root=RUNTIME/"executions"/execution_id; root.mkdir(parents=True)
 raw=RUNTIME/"raw"/f"{execution_id}.txt"; safe=RUNTIME/"sanitized"/f"{execution_id}.sanitized.txt"; raw.parent.mkdir(parents=True,exist_ok=True); safe.parent.mkdir(parents=True,exist_ok=True)
 try:
  command=[shutil.which("powershell") or "powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(ROOT/"tools/live-validation/run-automation-foundation.ps1"),"-WorkflowId","ZT-CV-WF-001","-Mode","ExecuteReadOnly","-OutputDirectory",".runtime/zero-trust/automation/repeatable-validation","-VerboseOutput"]
  completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=900,check=False,shell=False); raw.write_text(completed.stdout+completed.stderr,encoding="utf-8")
  subprocess.run([sys.executable,str(ROOT/"tools/live-validation/sanitize-live-evidence.py"),"--input",str(raw),"--output",str(safe)],cwd=ROOT,check=True,capture_output=True,text=True)
  bad=sanitizer_findings(safe.read_text(encoding="utf-8",errors="replace")); text=safe.read_text(encoding="utf-8",errors="replace")
  match=re.search(r"execution_id=(ZTA-[A-Za-z0-9-]+)",text); automation_id=match.group(1) if match else None; source=ROOT/".runtime/zero-trust/automation/executions"/str(automation_id)/"execution-record.json"; auto=load(source) if automation_id and source.is_file() else {}
  counts={state:sum(x.get("outcome")==state for x in auto.get("steps",[])) for state in ("PASS","WARN","FAIL")}
  security=verify_security_boundary(campaign)
  if completed.returncode!=0 or counts["FAIL"]: security["status"]="FAIL"
  authority="WINDOWS_TASK_SCHEDULER_EXECUTED_LIVE_RUNTIME" if scheduled_trigger else "CODEX_EXECUTED_LIVE_RUNTIME"
  limitation="Scheduled-trigger candidate; scheduler correlation and explicit review are required before history credit." if scheduled_trigger else "Manual campaign run; no schedule or authoritative update."
  f=campaign["fingerprints"]; record={"campaign_id":"ZT-RV-001","execution_id":execution_id,"execution_timestamp":iso(now),"execution_authority":authority,"execution_mode":"EXECUTE_READ_ONLY","capability_id":"ZT-4.1.1","package_id":"ZT-RV-001","validator_id":"ZTCV-VAL-SYS","workflow_id":"ZT-CV-WF-001","validator_version":f["validator_version"],"action_catalog_version":f["action_catalog_version"],"workflow_catalog_version":f["workflow_catalog_version"],"policy_version":f["policy_version"],"plan_hash":f["expected_plan_hash"],"target_scope_fingerprint":f["target_scope_fingerprint"],"raw_evidence_reference":str(raw.relative_to(ROOT)).replace('\\','/'),"sanitized_evidence_reference":str(safe.relative_to(ROOT)).replace('\\','/'),"raw_evidence_hash":sha(raw),"sanitized_evidence_hash":sha(safe),"sanitization_status":"FAIL" if bad else "PASS","pass":counts["PASS"],"warn":counts["WARN"],"fail":counts["FAIL"],"exit_code":completed.returncode,"warning_categories":observed_warning_categories(source.parent) if counts["WARN"] else [],"security_boundary":security,"limitations":[limitation],"source_automation_execution_id":automation_id,"scheduled_trigger_claim":scheduled_trigger}
  record["execution_fingerprint"]=execution_fingerprint(record); write(root/"execution-record.json",record); print(f"[{'PASS' if completed.returncode==0 and not bad else 'FAIL'}] execution_id={execution_id} pass={counts['PASS']} warn={counts['WARN']} fail={counts['FAIL']} candidate={root/'execution-record.json'}")
  return 0 if completed.returncode==0 and not bad else 1
 finally:
  if lock.exists(): lock.unlink()

def main()->int:
 p=argparse.ArgumentParser(description=__doc__); modes=p.add_mutually_exclusive_group(); modes.add_argument("--check",action="store_true"); modes.add_argument("--plan",action="store_true"); modes.add_argument("--execute-read-only",action="store_true"); modes.add_argument("--assess",action="store_true"); p.add_argument("--assessment-time"); p.add_argument("--scheduled-trigger",action="store_true"); p.add_argument("--verbose",action="store_true"); a=p.parse_args();
 if not any((a.check,a.plan,a.execute_read_only,a.assess)): a.check=True
 c=load(CAMPAIGN); errors=validate_configuration(c,load(POLICY))
 for item in errors: print(f"[FAIL] {item}")
 if errors: return 1
 if a.scheduled_trigger and not a.execute_read_only: print("[FAIL] --scheduled-trigger requires --execute-read-only"); return 2
 if a.check: print("[PASS] ZT-RV-001 campaign configuration is valid; no live execution or history update performed."); return 0
 plan=expected_plan(c)
 if a.plan: print(json.dumps(plan,indent=2)); print("[PASS] deterministic plan generated; no live execution or history update performed."); return 0
 if a.execute_read_only: return execute(c,a.verbose,a.scheduled_trigger)
 now=parse_time(a.assessment_time) if a.assessment_time else utcnow(); records=campaign_records(load(HISTORY)); result=assess(records,c,now); output=RUNTIME/"assessments/ZT-RV-001-assessment.yaml"; write(output,result); print(f"[PASS] assessment={result['acceptance']['result']} accepted={result['execution_history']['accepted']} continuity={result['current_continuity']} output={output}"); return 0
if __name__=="__main__": raise SystemExit(main())
