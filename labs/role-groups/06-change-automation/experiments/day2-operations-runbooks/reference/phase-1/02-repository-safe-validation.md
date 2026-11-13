# Repository-Safe Validation

```json runbook-metadata
{"runbook_id":"RB-P1-002","phase":"PHASE_1","related_packages":["ZT-FND-001"],"procedure_status":"IMPLEMENTED","validation_status":"VALIDATED_LOCAL","live_execution_permitted":false}
```

## Purpose

Run deterministic read-only package, capability, architecture, runbook, synchronization, report, structure, safety, and unit-test validation without mutating repository authority.

## Procedure

1. Capture a repository state fingerprint.
2. Run `validate_scenario_retirement.py` despite its historical action name; it verifies the package-oriented repository and absence of the retired framework.
3. Run Zero Trust, synchronization, report-check, architecture, runbook, and structure validators.
4. Run package-specific validators and the complete Python test suite.
5. Run secret, privacy, tracked-runtime, stale-reference, and diff checks.
6. Compare the final repository fingerprint with the initial fingerprint.

## Exit semantics

- 0: validation passed
- 1: content or policy failure
- 2: execution or repository-integrity failure

## Pass criteria

All required gates pass, the repository remains unchanged, and no live target or generated tracked runtime is touched.
