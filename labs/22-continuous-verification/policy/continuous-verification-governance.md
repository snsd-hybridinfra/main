# Continuous Verification Governance

The machine-readable authorities for `ZT-CV-001` are the continuous
verification policy, freshness policy, capability acceptance catalog, package
gates, regression policy, exception policy, maturity reassessment policy, and
verification history under `docs/zero-trust/`.

Acceptance defaults to deny when a validator, workflow, evidence file,
execution authority, freshness state, or dependency is unresolved. Warnings
remain visible and cannot be converted to passes merely to advance a gate.
Exceptions require an owner, reason, bounded scope, approval reference,
expiration, compensating control, and closure evidence. No active exception
exists in this baseline.

The evidence continuity levels are cumulative but never inferred from a plan:
EC3 requires one actual accepted runtime execution; EC4 requires three
independent consecutive successes with stable validator, workflow, scope, plan
and sanitization; EC5 additionally requires actual scheduled triggers on at
least three distinct dates. EC6 and EC7 require operational observation and
enforcement evidence beyond this package.

Maturity reassessment is proposal-only and capability-specific. Target
maturity, backlog position, reference frequency, package acceptance, and one
lab execution cannot assign current maturity or repository-wide compliance.

The 2026-07-27 normalized-flow cycle is intentionally recorded as `BLOCKED`:
the latest FND execution has one warning while its gate allows zero. This is a
successful detection of a prerequisite conflict, not an accepted CV result.
No RV or scheduled execution may inherit credit from that cycle.
