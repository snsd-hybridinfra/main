# Lab 23: Cloud Cost & Resource Cleanup Guardrails

**Status:** `MIGRATED / NOT_REVALIDATED`. YAML/JSON/Markdown policy templates only; **no policy engine or live cloud billing integration was included**.

## Question
Can synthetic infrastructure cost estimates and resource metadata be checked against budgets, ownership, approval exceptions, retention and safe cleanup rules?

## Contents
`fixtures/` holds 14 reusable source files for cost thresholds, approval exceptions, cleanup decisions and synthetic `PASS`/`FAIL`/`BLOCKED` inputs.

## Reproduction plan
1. Replace unquoted placeholder tokens and retired scenario references with **well-formed fixtures** suitable for strict YAML parsing.
2. Implement a small deterministic evaluator that reads the input records, applies owner/retention/dependency checks and returns an explicit allow/deny/review result.
3. Tests must confirm `CLEANUP_BLOCKED` on active retention, missing dependencies, and approvals not yet granted.
4. **No automatic delete operation in this lab.** External cloud APIs, credentials and spending data are not migrated.

Link to Lab 15 (AWS VPC), Lab 16 (OpenStack), Lab 14 (Terraform validation) after independent tests.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops`, commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `cost-governance/`.
