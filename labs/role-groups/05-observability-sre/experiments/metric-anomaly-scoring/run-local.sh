#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .outputs
python3 scripts/metric-dataset-normalization.example.py --input datasets/ml-metric-dataset-synthetic.sample.csv
python3 scripts/metric-anomaly-detection.example.py \
  --input datasets/ml-metric-dataset-synthetic.sample.csv \
  --output .outputs/detection.csv \
  --profile models/ml-anomaly-threshold-profile.example.yml
python3 scripts/anomaly-report-generation.example.py \
  --input .outputs/detection.csv \
  --metadata models/ml-anomaly-threshold-profile.example.yml \
  --output .outputs/report.md \
  --summary-output .outputs/summary.json
echo "Generated synthetic outputs in .outputs/"
