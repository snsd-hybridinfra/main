# Repeatable and Scheduled Validation

```json runbook-metadata
{"runbook_id":"RB-P1-007","phase":"PHASE_1","related_packages":["ZT-CV-001","ZT-RV-001","ZT-SCH-001"],"procedure_status":"PARTIALLY_IMPLEMENTED","validation_status":"PARTIALLY_RUNTIME_VALIDATED","live_execution_permitted":false}
```

## Purpose

Define and operate the bounded read-only cross-capability gate, then preserve
the separate predecessor gates for repeatable and scheduled validation.

## Current boundary

ZT-CV-001 is `IMPLEMENTED / PARTIALLY_RUNTIME_VALIDATED /
PARTIALLY_ACCEPTED` at EC3. Its 2026-07-28 cycle completed 8 PASS / 2 WARN /
0 FAIL with zero blocked gates. ZT-RV-001 is `IMPLEMENTED / VALIDATED /
ACCEPTED` at bounded EC4 after three eligible independent successes with
stable fingerprints and enforced separation. ZT-SCH-001 is `IMPLEMENTED /
LOCAL_VALIDATED / RUNTIME_NOT_VALIDATED`: its bounded Windows Task Scheduler
job is installed and disabled. Eleven sanitized candidates are retained: two
uncorrelated successes and nine failures, with zero accepted scheduled dates.
The bounded 09:00-11:00 `StartWhenAvailable` definition is preserved, but SCH
has been moved to the final Phase 5 gate immediately before P5-ACC-001. No
accepted scheduled runtime, CI workflow, automatic retry, or notification
integration exists.

## Required sequence

1. CV validates FND, NET, VIS, and ID together and records conflicts or missing controls.
2. RV repeats an accepted deterministic CV plan and proves evidence consistency.
3. P1-ACC-001 preserves the stale RV result and uses `P1-RV-FRESHNESS-001` only for Phase 2 local entry; the exception supplies no EC5 or scheduled-runtime credit.
4. SCH remains disabled until the separately approved final Phase 5 gate, where it must detect missed or failed runs, verify freshness and retention, and support disable and rollback.

## Pass criteria

CV passes only when every mandatory predecessor gate is accepted in the same
assessment. RV accepts only unique, sanitized, fingerprint-consistent runs
with zero blocking failures and at least 24 hours of separation. The current
RV state is accepted at 3/3 and bounded EC4. The installed disabled schedule
has zero successful correlated dates and therefore no runtime or EC5 credit;
seven non-RV evidence streams currently require freshness review. Phase 1 is
COMPLETED_WITH_GAPS, while stale RV evidence remains mandatory final-gate work at the ZT-RV-001 boundary.
