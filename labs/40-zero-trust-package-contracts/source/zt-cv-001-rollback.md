# ZT-CV-001 Rollback

`ZT-CV-001` performs no infrastructure or repository-authority mutation, so
runtime rollback is limited to operator-reviewed removal of generated files
under `.runtime/zero-trust/continuous-verification/` and the corresponding
automation execution directory. Historical tracked evidence must not be
deleted to hide a failure.

If a validator, workflow, schema, or policy change is rejected, restore only
that reviewed repository change through normal version control and rerun the
local validators. Do not rewrite verification history, reuse execution IDs,
or grant continuity credit to a superseded plan. Any VM or virtual-network
remediation remains a separate package-owned, explicitly approved action.

No service restart, scheduled-task deletion, credential change, access-control
rollback, automatic remediation, or authoritative maturity update is part of
this rollback procedure.
