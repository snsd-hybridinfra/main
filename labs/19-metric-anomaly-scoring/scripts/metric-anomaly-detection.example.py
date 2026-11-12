"""SAMPLE / NON-PRODUCTION deterministic local scoring; no network or training."""
import argparse
import csv
from pathlib import Path
import sys

REQUIRED = {"dataset_id", "metric_timestamp", "feature_group", "feature_name", "metric_name", "metric_value", "normalized_value", "evidence_reference"}
FIELDS = ["detection_run_id", "dataset_id", "metric_timestamp", "feature_group", "feature_name", "metric_name", "metric_value", "normalized_value", "baseline_value_placeholder", "anomaly_score", "threshold_reference", "anomaly_decision", "review_required", "related_scenario", "evidence_reference"]

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--input", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--profile", type=Path, required=True); a = p.parse_args()
    if not a.profile.is_file(): return 1
    with a.input.open(newline="", encoding="utf-8-sig") as f: rows = list(csv.DictReader(f))
    if not rows or REQUIRED.difference(rows[0]): return 1
    out=[]; anomalies=warnings=reviews=0
    for row in rows:
        try: value=float(row["metric_value"]); score=abs(float(row["normalized_value"]))
        except ValueError: return 1
        if score >= .8: decision="ANOMALY_DETECTED"; anomalies+=1
        elif score >= .6: decision="REVIEW_REQUIRED"; reviews+=1
        elif score >= .5: decision="WARNING"; warnings+=1
        else: decision="NORMAL"
        out.append({"detection_run_id":"<detection-run-id-placeholder>","dataset_id":row["dataset_id"],"metric_timestamp":row["metric_timestamp"],"feature_group":row["feature_group"],"feature_name":row["feature_name"],"metric_name":row["metric_name"],"metric_value":value,"normalized_value":score,"baseline_value_placeholder":"<baseline-placeholder>","anomaly_score":score,"threshold_reference":"<threshold-profile-placeholder>","anomaly_decision":decision,"review_required":str(decision != "NORMAL").lower(),"related_scenario":"synthetic-lab-case","evidence_reference":row["evidence_reference"]})
    with a.output.open("w", newline="", encoding="utf-8") as f: w=csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(out)
    print(f"rows processed={len(out)} anomaly count={anomalies} warning count={warnings} review required count={reviews}")
    return 0
if __name__ == "__main__": sys.exit(main())
