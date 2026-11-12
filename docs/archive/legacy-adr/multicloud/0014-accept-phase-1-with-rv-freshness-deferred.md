# ADR: Accept Phase 1 with RV Freshness Deferred

- Status: Accepted
- Date: 2026-08-20
- Scope: P1-ACC-001 and Phase 2 entry

## Context

P1-ACC-001 correctly default-denied on 2026-08-20 because all three reviewed
ZT-RV-001 records exceeded the P7D freshness limit. The historical campaign is
still a valid record of three separated, deterministic executions at its
original assessment time, but it does not prove current EC4 freshness.

The operator explicitly approved bypassing a new Phase 1 RV window for now and
continuing into Phase 2. Repeating the manual window would require three new
eligible executions separated by at least PT24H and would delay the central
identity and visibility work without changing their local design prerequisites.

## Decision

Phase 1 is accepted as `COMPLETED_WITH_GAPS` under exception
`P1-RV-FRESHNESS-001`. The historical P1-ACC-001 blocked decision remains
preserved; a superseding acceptance record grants only Phase 2 entry.

The exception does not mark stale RV evidence fresh, restore current EC4,
change ZT-RV-001 policy, or grant EC5. Fresh repeatability must be re-established
before the deferred final scheduled-validation gate and the final L3 decision.
ZT-SCH-001 remains installed and disabled.

Phase 2 starts with local preparation for P2-VIS-001. Live infrastructure,
service deployment, identity mutation, and live validators still require their
own explicit approval and preflight.

## Consequences

- M2 and Phase 1 may close with an explicit evidence-freshness gap.
- Phase 2 may start, but cannot inherit a current EC4 or EC5 claim.
- Gap ZG-016 remains open as accepted residual risk and becomes a mandatory
  final-gate prerequisite.
- Historical evidence, failures, package fingerprints, and policy thresholds
  remain unchanged.
- No maturity, compliance, certification, production readiness, or full-success
  claim is authorized.

## Rollback

Withdraw the superseding acceptance and return P1-ACC-001 to
`BLOCKED_STALE_EVIDENCE` if the exception scope is exceeded, Phase 2 attempts to
inherit current EC4, or the final gate no longer requires fresh RV evidence.
Preserve all decision and runtime history.
