#!/usr/bin/env python3
"""Evaluate package gates and emit a non-authoritative assessment."""
import argparse
from pathlib import Path
from cv_common import PATHS,RUNTIME,freshness_results,iso,load,package_acceptance_results,parse_time,repeatability_results,utcnow,write_json

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assessment-time"); p.add_argument("--freshness",type=Path); p.add_argument("--repeatability",type=Path); p.add_argument("--output",type=Path,default=RUNTIME/"package-acceptance.json"); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); now=parse_time(a.assessment_time) if a.assessment_time else utcnow(); h=load(PATHS["history"]); f=load(a.freshness)["results"] if a.freshness else freshness_results(h,load(PATHS["freshness"]),now); r=load(a.repeatability)["results"] if a.repeatability else repeatability_results(h,f); results=package_acceptance_results(load(PATHS["gates"]),h,f,r)
    write_json(a.output,{"assessment_type":"PACKAGE_ACCEPTANCE","assessment_time":iso(now),"results":results,"accepted_or_partial":sum(x["assessment_state"] in {"ACCEPTED","PARTIALLY_ACCEPTED"} for x in results),"authoritative_update_performed":False})
    if a.verbose:
        for item in results: print(f"[{item['assessment_state']}] {item['package_id']} continuity={item['evidence_continuity']}")
    blocked=sum(x["assessment_state"] in {"NOT_ACCEPTED","BLOCKED","ACCEPTANCE_EXPIRED"} for x in results); review=sum(x["assessment_state"] == "REVIEW_REQUIRED" for x in results); print(f"[{'WARN' if blocked or review else 'PASS'}] package gates={len(results)} blocked={blocked} review_required={review} output={a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
