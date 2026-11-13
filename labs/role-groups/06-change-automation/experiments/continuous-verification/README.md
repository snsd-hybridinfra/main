# Lab 22: Continuous Verification & Evidence Freshness

**Status: `MIGRATED / NOT_REVALIDATED`**. Source code, validation helpers, and policy files migrated without runtime execution.

This is a source-focused lab for evidence-age classification, repeatability windows, regression signals and acceptance/re-assessment logic. It is **not yet a standalone running verification scheduler**.

## Contents
- `src/`: sixteen extracted Python scripts for continuous verification, repeatability, scheduled checks and report/event bookkeeping
- `policy/`: representative freshness/verification/regression/capability/maturity and acceptance YAML definitions

## Safety boundary
Some scripts write evidence, perform scheduling, or call original repository workflows and expect original fixed paths, schemas, registries and verification history. Only the core `cv_common.py` paths were locally adapted. **Do not execute scheduled or remote pathways** without refactoring; no source-run success applies here.
`verification-history.yaml` was deliberately **not copied** because it contains historical execution records rather than reusable policy. Populate synthetic history fixtures for this lab.

## Next
1. Build a complete local `policy/` mapping and synthetic history file; remove any missing Zero Trust dependencies.
2. Test `FRESH`/`AGING`/`STALE`/`EXPIRED`/`UNKNOWN` classification against fixed timestamps.
3. Add deterministic regression and repeatability tests, explicit failure/no-history behavior and evidence redaction checks.
4. Only then consider read-only scheduled execution and integrate with Lab 21 and Lab 18.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
