#!/usr/bin/env python3
"""Evaluate recorded evidence age without deleting or replacing evidence."""
import argparse
from pathlib import Path
from cv_common import PATHS, RUNTIME, freshness_results, iso, load, parse_time, utcnow, write_json

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--assessment-time"); parser.add_argument("--output",type=Path,default=RUNTIME/"freshness.json"); parser.add_argument("--verbose",action="store_true"); args=parser.parse_args()
    now=parse_time(args.assessment_time) if args.assessment_time else utcnow(); results=freshness_results(load(PATHS["history"]),load(PATHS["freshness"]),now)
    payload={"assessment_type":"EVIDENCE_FRESHNESS","assessment_time":iso(now),"results":results,"counts":{state:sum(x["freshness_status"]==state for x in results) for state in ["FRESH","AGING","STALE","EXPIRED","UNKNOWN"]},"evidence_deleted":False,"authoritative_update_performed":False}; write_json(args.output,payload)
    if args.verbose:
        for item in results: print(f"[{item['freshness_status']}] {item['execution_id']} age_seconds={item['age_seconds']}")
    bad=sum(item["freshness_status"] in {"EXPIRED","UNKNOWN"} for item in results); print(f"[{'WARN' if bad else 'PASS'}] freshness records={len(results)} blocking_or_unknown={bad} output={args.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
