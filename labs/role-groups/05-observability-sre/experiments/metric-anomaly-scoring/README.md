# Lab 19: Deterministic Metric Anomaly Scoring and Reporting

**Status:** `MIGRATED / NOT_REVALIDATED`. Extracted synthetic scripts/data are not evidence of deployment or machine-learning training.

## Goal
Read a synthetic metrics CSV, validate fields, score normalized metrics with static thresholds and emit a human-reviewable anomaly summary. Intended later for network/NMS-like counters, not real customer telemetry.

## Included material
- `scripts/metric-dataset-normalization.example.py`: CSV format/label checks (despite its filename it does **not** normalize data)
- `scripts/metric-anomaly-detection.example.py`: deterministic scoring with fixed thresholds: >=0.8 anomaly, >=0.6 review, >=0.5 warning. This is **not** an ML model.
- `scripts/anomaly-report-generation.example.py`: local summary generation; no LLM or automatic remediation
- `datasets/*.csv`: synthetic/invalid test datasets
- `models/ml-anomaly-threshold-profile.example.yml`: documentary profile; the current scoring script checks only that the file exists, **not its threshold settings**.

## Planned reproduction
```bash
bash run-local.sh
```
Produces `.outputs/detection.csv`, `.outputs/report.md`, and `.outputs/summary.json`. Outputs are ignored by Git. Dependencies are Python standard library only. Actual command execution and output checks are still required before state promotion.

## Important limitations
- Synthetic scores do not establish anomaly-detection accuracy, sensitivity, precision or false positive rates.
- Dataset timestamps and asset names are placeholders, not real event identities.
- The score uses absolute normalized values, not statistical training or dynamic baselines. It cannot infer equipment fault causes.
- The report script emits fixed prose templates; human review remains mandatory.
- Before integration, change profile handling to enforce configured thresholds, add unit tests for invalid data/false positives, and build network-specific features (errors, discards, drops, utilization, route changes, link flaps).

## Provenance
Derived from `snsd-hybridinfra/snsd-multicloud-ops` at commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, directory `ml-security/`. Retired scenario labels were generalized, with original algorithm limitations explicitly documented.
