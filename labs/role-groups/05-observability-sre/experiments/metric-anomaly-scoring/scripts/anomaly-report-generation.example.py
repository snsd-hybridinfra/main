"""SAMPLE / NON-PRODUCTION deterministic report generation; no network or LLM."""
import argparse
import csv
import json
from pathlib import Path
import sys

REQUIRED={"detection_run_id","dataset_id","metric_timestamp","feature_group","feature_name","metric_name","metric_value","anomaly_score","anomaly_decision","review_required","related_scenario","evidence_reference"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--metadata",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--summary-output",type=Path);a=p.parse_args()
    with a.input.open(newline="",encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
    if not rows or REQUIRED.difference(rows[0]) or not a.metadata.is_file(): return 1
    anomalies=sum(r["anomaly_decision"]=="ANOMALY_DETECTED" for r in rows);warnings=sum(r["anomaly_decision"]=="WARNING" for r in rows);reviews=sum(r["review_required"].lower()=="true" for r in rows)
    report=f"""# ML Anomaly Report — SAMPLE / NON-PRODUCTION
## Report Metadata
report_id: `<report-id-placeholder>`
## Executive Summary
anomalies: {anomalies}; warnings: {warnings}; review-required: {reviews}
## Dataset Reference
synthetic-lab-case
## Detection Run Reference
synthetic-lab-case
## Anomaly Summary
Synthetic metric-only summary.
## Top Anomaly Candidates
`<anomaly-id-placeholder>`
## Affected Metric Groups
`<feature-group-placeholder>`
## Operational Interpretation
Deterministic sample text.
## Confidence / Review Notes
Human review is required before operational action.
## Recommended Operator Actions
Review sanitized evidence.
## Out-of-Scope Actions
No automated blocking; no LLM final decision.
## Evidence References
`<evidence-path>`
## Scenario Mapping
synthetic-lab-case / synthetic-lab-case / synthetic-lab-case
## Final Report Judgment
final_judgment: REPORT_READY
"""
    a.output.write_text(report,encoding="utf-8")
    if a.summary_output:a.summary_output.write_text(json.dumps({"report_id":"<report-id-placeholder>","dataset_source_scenario":"synthetic-lab-case","anomaly_detection_scenario":"synthetic-lab-case","final_evidence_report_scenario":"synthetic-lab-case","anomaly_count":anomalies,"warning_count":warnings,"review_required_count":reviews,"final_judgment":"REPORT_READY","evidence_reference":"<evidence-path>"},indent=2),encoding="utf-8")
    print(f"anomalies={anomalies} warnings={warnings} review_required={reviews}");return 0
if __name__=="__main__":sys.exit(main())
