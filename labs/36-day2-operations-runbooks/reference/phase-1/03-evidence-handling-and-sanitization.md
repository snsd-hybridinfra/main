# Evidence Handling and Sanitization

```json runbook-metadata
{"runbook_id":"RB-P1-003","phase":"PHASE_1","related_packages":["ZT-FND-001","ZT-NET-001","ZT-VIS-001","ZT-ID-001"],"procedure_status":"PARTIALLY_IMPLEMENTED","validation_status":"VALIDATED_LOCAL","live_execution_permitted":false}
```

## Purpose

Define how an approved package execution may produce a reviewed, sanitized, text-only evidence derivative.

## Rules

- The package and execution authority must exist before evidence collection.
- Raw output remains under ignored `.runtime/zero-trust/`.
- Remove secrets, credentials, keys, tokens, addresses, account identifiers, unnecessary host identities, and personal data.
- Record package ID, capability IDs, target class, executor class, validation class, result, limitations, source authority, sanitization result, and rollback or cleanup result.
- Reject evidence whose source, scope, or sanitization cannot be verified.
- Never promote implementation, acceptance, evidence continuity, compliance, or maturity from documentation alone.

## Pass criteria

The tracked derivative is minimal, resolvable, sanitized, package-owned, evidence-based, and explicit about limitations. Tracked runtime remains zero.
