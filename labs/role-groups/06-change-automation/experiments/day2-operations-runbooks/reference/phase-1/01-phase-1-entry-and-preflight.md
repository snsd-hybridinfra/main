# Phase 1 Entry and Preflight

```json runbook-metadata
{"runbook_id":"RB-P1-001","phase":"PHASE_1","related_packages":["ZT-FND-001"],"procedure_status":"IMPLEMENTED","validation_status":"VALIDATED_LOCAL","live_execution_permitted":false}
```

## Purpose

Establish a clean Git baseline, package authority, protected scope, read-only validation boundary, and stop conditions before package work.

## Procedure

1. Confirm branch, HEAD, origin/main, clean worktree, staged files, and Git operation markers.
2. Confirm no tracked `.runtime/**`, secret, private key, account value, or personal data.
3. Read scope, exclusions, package-flow authority, package metadata, evidence, and runbooks.
4. Verify the target package, predecessor, capability scope, execution authority, rollback, and expected evidence.
5. Record whether live execution is authorized. Default to repository-local read-only validation.
6. Stop on unrelated changes, ambiguous ownership, missing source authority, live target requirements, or unsupported status claims.

## Pass criteria

The repository baseline and package scope are explicit, protected data is absent, the operation is authorized, and no live action is implied by local validation.
