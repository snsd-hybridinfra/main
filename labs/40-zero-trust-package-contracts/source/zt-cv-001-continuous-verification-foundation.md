# ZT-CV-001 Continuous Verification Foundation

## Implemented boundary

`ZT-CV-001` implements a default-deny, fixed-handler framework for evidence
freshness, repeatability, package and capability acceptance, regression
detection, exception governance, and proposal-only maturity reassessment. The
tooling and fixed plan are implemented, and the bounded package is partially
accepted at EC3 with explicit gaps.

The runtime evidence level is `EC3_ONE_TIME_RUNTIME`. It is not continuous
verification in the operational `EC6` sense. It does not install a schedule,
execute a mutation, remediate a finding, update an authority automatically, or
assign maturity.

## Decision flow

1. Validate the Zero Trust and CV authorities.
2. Evaluate existing evidence freshness without deletion.
3. Run the fixed bounded live-system validator.
4. Calculate continuity from unique execution records.
5. Evaluate package and capability gates.
6. Detect regressions without remediation.
7. Produce a check-only maturity reassessment result.
8. Write sanitized output under the ignored runtime boundary.

Every step is registered in the reviewed automation catalogs. YAML does not
contain an executable command, arbitrary SSH target, or caller-controlled
working directory.

## Historical runtime result

The preserved pre-normalization execution is
`ZTA-20260722T045752Z-eb639d92` with plan hash
`72c0aa52f20b12fb67d7b149e7c1ed980c2cfcbcdafea9cfc344cac2f4912624`.
It completed 8 PASS / 2 WARN / 0 FAIL and remains historical EC3 evidence. It
does not override the current normalized-flow gate.

## Current normalized-flow decision

Execution `ZTA-20260728T082622Z-594aed64` used the same fixed plan hash and
completed `PARTIAL` with 8 PASS, 2 WARN, and 0 FAIL. Freshness assessment found
10 fresh records, 1 aging record, 1 preserved superseded stale record, and no
current regression. All ten package gates returned accepted or partially
accepted with zero blocked or review-required result. P1-CV-001 therefore
completes as `PASS_WITH_OPEN_GAPS` at EC3. Failed and superseded attempts
receive no acceptance or continuity credit.

All three OpenStack instances and all EVE node processes were returned to their
original stopped state. No target configuration, ACL, identity policy,
logging configuration, authority file, or schedule was changed by the live
workflow.

## Successor gate

`ZT-RV-001` is accepted at bounded EC4 with three eligible independent
executions. A copied record, immediate retry, failed run, changed plan, blocked
run, or unsanitized result does not count. `ZT-SCH-001` is now the next package,
but remains unimplemented until separate scheduler installation approval.
