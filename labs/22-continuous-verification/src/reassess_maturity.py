#!/usr/bin/env python3
"""Produce proposal-only capability maturity decisions."""
import argparse
from pathlib import Path
from cv_common import PATHS,RUNTIME,capability_acceptance_results,freshness_results,iso,load,maturity_results,parse_time,repeatability_results,utcnow,write_json

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assessment-time"); p.add_argument("--capability-results",type=Path); p.add_argument("--output",type=Path,default=RUNTIME/"maturity-reassessment.json"); p.add_argument("--check",action="store_true"); p.add_argument("--proposal",action="store_true"); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); now=parse_time(a.assessment_time) if a.assessment_time else utcnow()
    if a.capability_results: c=load(a.capability_results)["results"]
    else:
        h=load(PATHS["history"]); f=freshness_results(h,load(PATHS["freshness"]),now); c=capability_acceptance_results(load(PATHS["capabilities"]),h,f,repeatability_results(h,f))
    results=maturity_results(c); write_json(a.output,{"assessment_type":"MATURITY_REASSESSMENT_PROPOSAL","assessment_time":iso(now),"mode":"PROPOSAL_ONLY" if a.proposal else "CHECK_ONLY","results":results,"upgrades":0,"downgrades":0,"maturity_assigned":False,"authoritative_update_performed":False})
    print(f"[PASS] maturity decisions={len(results)} upgrades=0 downgrades=0 authoritative_updates=0 output={a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
