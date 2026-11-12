# Lab 21: Change Automation Approval & Policy Gates

**Status:** `MIGRATED / NOT_REVALIDATED`. Partial code relocation, no script executed.

## Goal
Classify infrastructure changes by risk and evaluate allow/deny/required-approval decisions before execution.

## Included
- `src/automation_common.py`, `evaluate_action_policy.py`, `plan_workflow.py`, `validate_automation_catalogs.py`: policy helpers; one root path adjusted for local catalog lookup
- `policy/`: source action/workflow catalogs and approval/governance policies
- `src/run_workflow.py`, `apply_approved_proposal.py`: **reference-only, DO NOT EXECUTE**. These may trigger actions and depend on source repository integrations not present here.

## Next
Refactor into a plan-only deterministic evaluator, add synthetic workflow fixtures and assertions for unauthorized/expired approval, block mutating handlers by default, and create audit/rollback expectations. Explicit user consent and a disposable environment are prerequisites for execution.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. Imported selectively; prior Zero Trust governance acceptance does not transfer.
