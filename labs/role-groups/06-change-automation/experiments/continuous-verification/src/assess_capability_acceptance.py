#!/usr/bin/env python3
"""Evaluate capability acceptance without changing the baseline authority."""
import argparse
from pathlib import Path
from cv_common import PATHS,RUNTIME,capability_acceptance_results,freshness_results,iso,load,parse_time,repeatability_results,utcnow,write_json

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assessment-time"); p.add_argument("--freshness",type=Path); p.add_argument("--repeatability",type=Path); p.add_argument("--output",type=Path,default=RUNTIME/"capability-acceptance.json"); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); now=parse_time(a.assessment_time) if a.assessment_time else utcnow(); h=load(PATHS["history"]); f=load(a.freshness)["results"] if a.freshness else freshness_results(h,load(PATHS["freshness"]),now); r=load(a.repeatability)["results"] if a.repeatability else repeatability_results(h,f); results=capability_acceptance_results(load(PATHS["capabilities"]),h,f,r)
    write_json(a.output,{"assessment_type":"CAPABILITY_ACCEPTANCE","assessment_time":iso(now),"results":results,"maturity_assigned":False,"authoritative_update_performed":False})
    review=sum(x["assessment_state"] in {"REVIEW_REQUIRED","NOT_ACCEPTED","BLOCKED"} for x in results); print(f"[{'WARN' if review else 'PASS'}] capability assessments={len(results)} review={review} output={a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
