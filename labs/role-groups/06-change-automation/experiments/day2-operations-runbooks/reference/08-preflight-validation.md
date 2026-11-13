
# Preflight Validation

## Purpose

Evaluate profile and host readiness.

## Scope

Target-architecture procedure only; no executable result is claimed.

## Supported target types

`openstack-vm`, `existing-vm`, and `physical-server` unless the selected adapter narrows support.

## Current implementation status

`DESIGN_SPECIFICATION`

## Current validation status

`NOT_IMPLEMENTED`

## Required authority

Codex manages repository and configuration work. The user performs only physical/manual prerequisites and supplies explicit approval for destructive or service-affecting action.

## Prerequisites

Approved target profile, applicable prior phase gate, rollback path, and external secret source.

## Inputs

Profile reference, operation ID, package version, plan hash where applicable, and approved change record.

## Secret inputs

Interactive or VM-local external input only. Do not place passwords, tokens, keys, client secrets, MFA material, or private cloud configuration in Git.

## Service impact

Read-only until a future procedure explicitly marks an approved mutating step. Deployment, recovery, rotation, replacement, and decommission may affect service.

## Security impact

The procedure may change enforcement or evidence state only after Policy as Code and approval gates pass.

## Preflight checks

Validate profile schema, host-onboarding state, dependencies, public exposure, approval requirement, rollback availability, validator availability, and evidence path.

## Procedure

1. Run the planned `platform` command in read-only preflight or plan mode.
2. Review deterministic findings and the plan hash.
3. Stop on `DENY`, `BLOCKED`, `NOT_READY`, stale evidence, or changed plan hash.
4. Obtain explicit approval when the operation is mutating or service-affecting.
5. Run the future package implementation only after it exists.
6. Validate, sanitize, and record the result.

Commands in this section are planned contracts until the related package implements them.

## Expected output

Structured status, affected capability IDs, policy result, immutable plan hash, safe evidence references, result counters, and limitations.

## Validation

Run the package-specific local validator and, when authorized, the bounded runtime validator. Documentation review alone is insufficient.

## Pass criteria

Preflight and policy pass, approval matches the plan hash, runtime validation passes where required, rollback is available, and evidence sanitization passes.

## Stop conditions

Any secret exposure, unapproved public exposure, policy denial, missing rollback, unavailable validator, changed plan, destructive ambiguity, or sanitization failure.

## Failure handling

Preserve raw output only in the ignored runtime area, record the failing gate, make no acceptance claim, and generate a non-mutating remediation proposal.

## Rollback

Use the last accepted version or package-specific rollback after explicit approval. If rollback is not implemented or not validated, stop and mark the operation `BLOCKED`.

## Evidence

Record authority, timestamp, policy version, plan hash, configuration version, target profile, validator version, counters, limitations, and sanitized reference. Raw output remains under `.runtime/zero-trust/`.

## Escalation

Escalate physical access, interactive secret entry, destructive approval, service-impact approval, or a scope/architecture conflict to the user. Codex retains repository work.

## Known limitations

This procedure is not runtime validated and may reference future package commands that do not yet exist.

## Related architecture

`docs/zero-trust/target-architecture/README.md`

## Related package

`ZT-ONB-001` (`PLANNED` unless an existing package record states otherwise)
