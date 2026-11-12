# ADR: Defer Scheduled Validation to the Final Project Gate

- Status: Accepted
- Date: 2026-08-20
- Scope: Phase 1 package flow and ZT-SCH-001 execution order

## Context

ZT-RV-001 already provides three reviewed, separated, deterministic executions
and is accepted at bounded EC4. The installed ZT-SCH-001 task added daily
scheduler operation, but its results depended on an interactive Windows session
and laboratory availability. Eleven scheduled candidates were retained: two
passed the read-only workflow but were not scheduler-correlated, while nine
failed. The most recent failures were caused by a router external-path check and
an unavailable OpenStack SSH endpoint rather than a change to the accepted
Phase 1 control implementations.

Keeping scheduled-runtime EC5 as the next Phase 1 predecessor consumed project
time without advancing the implementation workstreams. The operator therefore
approved moving scheduled validation to the final project gate.

## Decision

ZT-SCH-001 is removed from the sequential Phase 1 flow. Phase 1 now ends its
technical package sequence at the accepted bounded ZT-RV-001 EC4 result and
then proceeds to P1-ACC-001. Phase 1 remains `PARTIAL /
PARTIALLY_VALIDATED / NOT_COMPLETE` until that explicit acceptance action is
performed; this decision does not itself complete or promote Phase 1.

The existing `P1-SCH-001` action identifier is retained for history and evidence
continuity, but the action is moved to the final Phase 5 gate immediately before
P5-ACC-001. ZT-SCH-001 remains an authoritative implemented and locally
validated package with runtime validation `NOT_VALIDATED`, acceptance `PENDING`,
continuity EC4, and maturity `UNASSESSED`.

The installed Windows task is disabled, not deleted. Its definition, ignored
runtime records, failures, and uncorrelated successes are preserved. Re-enabling
or replacing it requires a new explicit approval during the final project gate.

## Consequences

- Phase 1 work can proceed to P1-ACC-001 without claiming EC5.
- Scheduled runtime is still required before the final L3 project decision.
- No historical evidence is rewritten and no failed run becomes accepted.
- No automatic retry, remediation, infrastructure mutation, repository
  mutation, status promotion, maturity assignment, or compliance claim is
  authorized.
- The scheduler correlation timezone defect remains an open final-gate issue and
  must be repaired and regression-tested before scheduled evidence is accepted.

## Rollback

Restore ZT-SCH-001 as a Phase 1 predecessor only through another approved ADR,
then synchronize the package flow, execution plan, roadmap, validators, and
status authorities. Re-enable the installed task only with a separate explicit
scheduler approval. Preserve all existing runtime and Git history in either
direction.
