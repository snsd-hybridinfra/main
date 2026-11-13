#!/usr/bin/env python3
"""Assess execution continuity from unique recorded runs only."""
import argparse
from pathlib import Path
from cv_common import PATHS,RUNTIME,freshness_results,iso,load,parse_time,repeatability_results,utcnow,write_json

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assessment-time"); p.add_argument("--freshness",type=Path); p.add_argument("--output",type=Path,default=RUNTIME/"repeatability.json"); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); now=parse_time(a.assessment_time) if a.assessment_time else utcnow(); history=load(PATHS["history"])
    fresh=load(a.freshness)["results"] if a.freshness else freshness_results(history,load(PATHS["freshness"]),now); results=repeatability_results(history,fresh); counts={level:sum(x["evidence_continuity"]==level for x in results) for level in ["EC3_ONE_TIME_RUNTIME","EC4_REPEATABLE_RUNTIME","EC5_SCHEDULED_RUNTIME"]}
    write_json(a.output,{"assessment_type":"REPEATABILITY","assessment_time":iso(now),"results":results,"counts":counts,"scheduled_operation_claimed":False,"continuous_operation_claimed":False,"authoritative_update_performed":False})
    if a.verbose:
        for item in results: print(f"[{item['evidence_continuity']}] {item['group']['package_id']} count={item['execution_count']}")
    print(f"[PASS] repeatability groups={len(results)} EC4={counts['EC4_REPEATABLE_RUNTIME']} EC5={counts['EC5_SCHEDULED_RUNTIME']} output={a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
