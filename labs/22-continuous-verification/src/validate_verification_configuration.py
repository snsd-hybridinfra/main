#!/usr/bin/env python3
"""Validate ZT-CV-001 authorities and cross references without changing them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cv_common import PATHS, ROOT, load, parse_duration, parse_time

SCHEMAS = [
    "zero-trust-continuous-verification-policy.schema.json",
    "zero-trust-evidence-freshness-policy.schema.json",
    "zero-trust-capability-acceptance-catalog.schema.json",
    "zero-trust-package-acceptance-gates.schema.json",
    "zero-trust-verification-regression-policy.schema.json",
    "zero-trust-verification-exception-policy.schema.json",
    "zero-trust-maturity-reassessment-policy.schema.json",
    "zero-trust-verification-history.schema.json",
    "zero-trust-capability-acceptance-result.schema.json",
    "zero-trust-maturity-reassessment-result.schema.json",
]


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, dict] = {}
    for name, path in PATHS.items():
        try:
            data[name] = load(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: {exc}")
    if errors:
        return errors, warnings
    for schema in SCHEMAS:
        path = ROOT / "schemas" / schema
        try:
            value = load(path)
            if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"{schema}: wrong JSON Schema dialect")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{schema}: {exc}")
    policy = data["policy"]
    if policy.get("metadata", {}).get("default_decision") != "DENY_ACCEPTANCE_WITHOUT_EVIDENCE":
        errors.append("continuous verification must default deny acceptance")
    levels = [item.get("id") for item in policy.get("evidence_continuity_levels", [])]
    expected_levels = ["EC0_NONE","EC1_DESIGN","EC2_CONFIGURATION","EC3_ONE_TIME_RUNTIME","EC4_REPEATABLE_RUNTIME","EC5_SCHEDULED_RUNTIME","EC6_CONTINUOUS_OBSERVATION","EC7_CONTINUOUS_ENFORCEMENT"]
    if levels != expected_levels:
        errors.append("evidence continuity levels must be complete and ordered")
    validators = {item.get("id"): item for item in policy.get("validator_registry", [])}
    if len(validators) != 10 or None in validators:
        errors.append("validator registry must contain ten unique entries")
    for validator_id, validator in validators.items():
        if not (ROOT / str(validator.get("implementation", ""))).is_file():
            errors.append(f"{validator_id}: implementation does not resolve")
        if validator.get("mutation") is not False:
            errors.append(f"{validator_id}: mutation must be false")
    workflows = load(ROOT / "docs/zero-trust/automation-workflow-catalog.yaml")
    workflow_ids = {item.get("id") for item in workflows.get("workflows", [])}
    if "ZT-CV-WF-001" not in workflow_ids:
        errors.append("ZT-CV-WF-001 is not registered")
    capability_authority = load(ROOT / "docs/zero-trust/capability-catalog.yaml")
    capability_ids = {item.get("id") for item in capability_authority.get("capabilities", [])}
    gate_ids = {item.get("id") for item in data["gates"].get("gates", [])}
    for item in policy.get("policies", []):
        if any(value not in validators for value in item.get("required_validators", [])):
            errors.append(f"{item.get('id')}: unresolved validator")
        if item.get("acceptance_gate") not in gate_ids:
            errors.append(f"{item.get('id')}: unresolved acceptance gate")
        if any(value not in capability_ids for value in item.get("capability_ids", [])):
            errors.append(f"{item.get('id')}: unresolved capability")
        for field in ("freshness_window", "grace_period"):
            try: parse_duration(item[field])
            except (KeyError, ValueError) as exc: errors.append(f"{item.get('id')}: {exc}")
    package_ids = [item.get("package_id") for item in data["gates"].get("gates", [])]
    if len(package_ids) != 10 or len(package_ids) != len(set(package_ids)):
        errors.append("package gates must cover ten unique packages")
    gate_by_package = {item.get("package_id"): item for item in data["gates"].get("gates", [])}
    for package_id, gate in gate_by_package.items():
        for dependency in gate.get("depends_on", []):
            if dependency not in gate_by_package:
                errors.append(f"{package_id}: unresolved gate dependency {dependency}")
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(package_id: str) -> None:
        if package_id in visiting:
            errors.append(f"gate dependency cycle at {package_id}"); return
        if package_id in visited: return
        visiting.add(package_id)
        for dependency in gate_by_package.get(package_id, {}).get("depends_on", []): visit(dependency)
        visiting.remove(package_id); visited.add(package_id)
    for package_id in gate_by_package: visit(package_id)
    catalog_ids = [item.get("id") for item in data["capabilities"].get("capabilities", [])]
    if len(catalog_ids) != 12 or len(catalog_ids) != len(set(catalog_ids)) or any(item not in capability_ids for item in catalog_ids):
        errors.append("capability acceptance catalog must contain twelve resolvable unique capabilities")
    freshness_ids = {item.get("id") for item in data["freshness"].get("policies", [])}
    execution_ids: set[str] = set()
    for record in data["history"].get("executions", []):
        execution_id = record.get("execution_id")
        if execution_id in execution_ids: errors.append(f"duplicate execution ID: {execution_id}")
        execution_ids.add(execution_id)
        if record.get("package_id") not in gate_by_package and not (record.get("package_id") == "ZT-RV-001" and record.get("campaign_id") == "ZT-RV-001"):
            errors.append(f"{execution_id}: unresolved package")
        if record.get("validator_id") not in validators: errors.append(f"{execution_id}: unresolved validator")
        if record.get("workflow_id") not in workflow_ids: errors.append(f"{execution_id}: unresolved evaluator workflow")
        if record.get("freshness_policy_id") not in freshness_ids: errors.append(f"{execution_id}: unresolved freshness policy")
        if record.get("scheduled_trigger") is not False: errors.append(f"{execution_id}: historical record is not an installed schedule trigger")
        try: parse_time(str(record.get("execution_date", "")))
        except ValueError as exc: errors.append(f"{execution_id}: {exc}")
    for exception in data["exceptions"].get("exceptions", []):
        if exception.get("state") == "APPROVED" and not exception.get("expiration"):
            errors.append(f"{exception.get('id')}: approved exception lacks expiration")
    if data["maturity"].get("metadata", {}).get("authority") != "ZT-CV-001":
        errors.append("maturity policy authority mismatch")
    maturity_text = json.dumps(data["maturity"], ensure_ascii=False)
    if "authoritative_update_performed" in maturity_text and 'true' in maturity_text.lower():
        errors.append("maturity policy authorizes an authoritative write")
    warnings.append("Reference frequencies are governance targets only; no schedule is installed.")
    warnings.append("Existing history is EC3 at most; repeatability and continuity are not inferred.")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate()
    for item in errors: print(f"[FAIL] {item}")
    if args.verbose:
        for item in warnings: print(f"[WARN] {item}")
    print(f"[{'FAIL' if errors else 'PASS'}] ZT-CV-001 configuration: errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
