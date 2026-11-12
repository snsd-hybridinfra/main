# Lab 40: Zero Trust Package Contracts & Rollback Criteria

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. All **38 original files** under `docs/zero-trust/packages/` were extracted, including capability/package definitions, rollout boundaries and rollback notes.

## Purpose
Transform cross-cutting Zero Trust packages into small, independently testable controls while retaining the original acceptance, dependency and rollback intent.

## Suggested exercises
1. Parse each package contract and map `required_evidence`, `precondition`, `denied_actions` and `rollback` into synthetic test matrices.
2. Cover access, application, automation, device, data and continuous verification, using Labs 21–22, 31–32 and 38 as supporting sources.
3. Make every test fail closed for missing evidence or policy exceptions.
4. Verify a rollback scenario in a disposable lab only. No live deployment, no customer assets and no claims of achieved maturity/compliance.

## Critical limitations
Package design documents are **not** evidence that runtime enforcement is implemented. Some original packages reference remote validators and repo-specific policy catalogs not copied into this lab. No status is promoted based on their presence.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `docs/zero-trust/packages/`.
