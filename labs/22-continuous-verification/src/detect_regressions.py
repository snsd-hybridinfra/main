#!/usr/bin/env python3
"""Detect evidence and execution regressions; never remediate them."""
import argparse
from pathlib import Path
from cv_common import PATHS,RUNTIME,freshness_results,iso,load,parse_time,regression_results,utcnow,write_json

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assessment-time"); p.add_argument("--freshness",type=Path); p.add_argument("--output",type=Path,default=RUNTIME/"regressions.json"); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); now=parse_time(a.assessment_time) if a.assessment_time else utcnow(); h=load(PATHS["history"]); f=load(a.freshness)["results"] if a.freshness else freshness_results(h,load(PATHS["freshness"]),now); findings=regression_results(h,f)
    write_json(a.output,{"assessment_type":"REGRESSION_DETECTION","assessment_time":iso(now),"findings":findings,"count":len(findings),"remediation_performed":False,"authoritative_update_performed":False})
    if a.verbose:
        for item in findings: print(f"[WARN] {item['type']} {item['reason']}")
    print(f"[{'WARN' if findings else 'PASS'}] regressions={len(findings)} output={a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
