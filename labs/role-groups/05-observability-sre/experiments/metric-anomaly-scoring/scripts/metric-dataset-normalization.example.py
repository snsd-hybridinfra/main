"""SAMPLE / NON-PRODUCTION CSV validation helper; no network or ML runtime."""

import argparse
import csv
from pathlib import Path
import sys

REQUIRED = {
    "dataset_id", "metric_timestamp", "metric_name", "metric_value",
    "normalized_value", "anomaly_label_placeholder", "collection_method",
}
LABELS = {"normal", "suspected_anomaly", "unknown"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    missing = REQUIRED.difference(rows[0].keys() if rows else set())
    errors = []
    for index, row in enumerate(rows, start=1):
        try:
            float(row["metric_value"])
            float(row["normalized_value"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"row {index}: numeric validation failed")
        if row.get("anomaly_label_placeholder") not in LABELS:
            errors.append(f"row {index}: invalid label")
    print(f"rows={len(rows)} missing_columns={len(missing)} errors={len(errors)}")
    return 1 if missing or errors else 0


if __name__ == "__main__":
    sys.exit(main())
