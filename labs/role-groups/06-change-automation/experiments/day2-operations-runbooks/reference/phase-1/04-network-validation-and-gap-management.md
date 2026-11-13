# Network Validation and Gap Management

```json runbook-metadata
{
  "runbook_id": "RB-P1-004",
  "title": "Network Validation and Gap Management",
  "phase": "PHASE_1",
  "related_packages": ["ZT-NET-001"],
  "owner_domain": "NETWORK_SECURITY",
  "supported_target_types": ["REPOSITORY_LOCAL", "BOUNDED_NON_PRODUCTION_EVE_NG_ROUTER"],
  "procedure_status": "IMPLEMENTED",
  "validation_status": "RUNTIME_VALIDATED",
  "runtime_required": true,
  "live_execution_permitted": true,
  "required_authority": "EXPLICIT_OPERATOR_APPROVAL_AND_EXISTING_RESTRICTED_ENDPOINT",
  "evidence_authority": "CODEX_EXECUTED_LIVE_RUNTIME",
  "last_reviewed": "2026-07-27",
  "limitations": ["One persistent directional ACL is validated; broader multi-zone segmentation, dynamic policy, encryption, and resilience remain outside the bounded package."]
}
```

## Purpose

Revalidate the accepted bounded ZT-NET-001 network evidence safely without
changing the accepted router policy.

## Scope

Existing forced-command read-only router validation, static package checks,
evidence review, and accepted ACL-state verification. Configuration and
remediation remain outside this revalidation runbook.

## Related Phase

Phase 1; ZT-NET-001 is implemented, runtime validated, and accepted for its bounded directional inter-zone ACL scope.

## Related Package or Governance Action

ZT-NET-001 package, validation record, rollback record, and current baseline.

## Supported Target Types

Repository-local package records and the already established bounded
non-production EVE-NG router restricted endpoint.

## Current Procedure Status

`IMPLEMENTED`: read-only validation and accepted persistent ACL evidence exist.

## Current Validation Status

`RUNTIME_VALIDATED` for the bounded package; runtime validation is `VALIDATED`, acceptance is `ACCEPTED`, and capability maturity is unchanged.

## Evidence Authority

Existing package authority is `CODEX_EXECUTED_LIVE_RUNTIME`. This action does
not create new live authority.

## Required Authority

Repository-local inspection needs no extra approval. Any new live invocation
requires explicit operator approval and the existing fixed restricted endpoint.
Any configuration change requires a separate mutating action and rollback plan.

## User-Performed Physical or Approval Steps

Approve any future live revalidation and separately approve any change to the
accepted ACL after reviewing blast radius and rollback.

## Codex or Automation-Managed Steps

Validate package records locally, invoke only the approved fixed read-only
command when separately authorized, sanitize output, and preserve the accepted
policy boundary.

## Prerequisites

RB-P1-001 ready; ZT-FND-001 restricted endpoint boundary intact; ZT-NET-001
records consistent; fixed alias available; required EVE router and switch nodes
and the fixed OpenStack test path may be started only for an approved run;
source evidence and sanitization path approved.

## Inputs

Package metadata, existing validation record, fixed command contract, router
identity classification, expected check set, and gap register.

## Secret Inputs

None in Git or command arguments. Interactive credentials, router
configuration, raw addresses, MAC inventories, and private keys are prohibited.

## Service Impact

The approved validator is read-only. Persistent ACL configuration could affect
connectivity and is not authorized by this runbook.

## Security Impact

The restricted endpoint blocks interactive shell, arbitrary commands,
configuration commands, and arbitrary ping. Weakening that boundary is a stop.

## Preflight Checks

Confirm package state `IMPLEMENTED` / `RUNTIME_VALIDATED`, runtime validation
`VALIDATED`, current maturity `UNASSESSED`, fixed alias/command, BatchMode,
existing rollback record, sanitized destination, and accepted classification
`BOUNDED_INTERZONE_ACL_VALIDATED`.

## Procedure

1. Validate ZT-NET-001 machine records and references locally.
2. Review the accepted bounded results: identity, interfaces, routing, NAT,
   persistent interface ACL binding, allow/deny behavior, and startup state.
3. If a separately approved live revalidation exists, invoke only this command.

```json command-metadata
{
  "command": "ssh -o BatchMode=yes snsd-r1-validator validate-routing",
  "command_status": "LIVE_RUNTIME_REQUIRED",
  "execution_owner": "CODEX_OR_AUTOMATION",
  "approval_required": true,
  "runtime_target": "BOUNDED_NON_PRODUCTION_EVE_NG_ROUTER",
  "expected_effect": "Read fixed router-observable validation data through the restricted dispatcher; no configuration change.",
  "evidence_output": "Ignored raw output and a reviewed sanitized ZT-NET-001 derivative.",
  "rollback_reference": "docs/zero-trust/packages/zt-net-001-rollback.md"
}
```

4. Preserve segmentation classification as
   `BOUNDED_INTERZONE_ACL_VALIDATED` unless new accepted evidence proves
   otherwise.
5. Do not enter configuration mode, change the accepted ACL, or test arbitrary
   targets during read-only revalidation.
6. Record only sanitized evidence under RB-P1-003.

## Expected Output

Package/reference status, bounded read-only check categories, sanitized
counters when a separately authorized run occurs, unchanged limitations, and
the accepted persistent ACL boundary. No fictional execution result is
produced here.

## Validation

Static validation checks package consistency and restricted wrapper semantics.
Runtime validation, when separately approved, must use the exact fixed command
and must confirm the security boundary as well as routing results.

The 2026-07-27 approved revalidation started only the existing bounded router,
switch, DMZ test node, and fixed OpenStack test instance. It returned 39 PASS,
0 WARN, and 0 FAIL; reproduced 5/5 gateway allow, 5/5 explicit Kubernetes
denial, and 5/5 provider-path allow; denied four endpoint bypass requests; and
restored every temporary runtime power state. No ACL or switch configuration
was written.

## Pass Criteria

Existing package facts remain consistent; restricted endpoint controls hold;
no configuration change occurs during revalidation; evidence is sanitized; the
accepted ACL binding remains present.

## Stop Conditions

Unapproved live request, non-fixed target or command, interactive shell,
configuration command, arbitrary ping, credential request, router identity
drift, service-impacting change, missing rollback, unsafe evidence, or proposal
to equate bounded macro separation with comprehensive per-workload enforcement.

## Failure Handling

Do not retry by broadening access. Classify transport, wrapper, router check,
sanitization, and evidence failures separately; downgrade current-run evidence
without rewriting the accepted historical result.

## Rollback

Read-only validation needs no network rollback. For repository-only record
errors, correct the bounded derivative through review. ACL changes are not part
of this runbook and require their own approved rollback.

## Evidence

Retain command contract, executor, bounded target class, counters, security
boundary, sanitization result, and limitations. Never commit raw configuration
or dynamic identifiers.

## Escalation

Escalate any ACL implementation proposal, connectivity risk, security-boundary
failure, unknown router state, or request for broader access.

## Known Limitations

The accepted scope covers one directional DMZ-to-Kubernetes policy only.
Broader micro-segmentation, SDN policy, encryption, and resilience require new
package approval, fixed-flow tests, persistence evidence, and tested rollback.

## Related Architecture

`docs/zero-trust/packages/zt-net-001-router-validation.md` and the Phase 1
dependency map.

## Related Runbooks

RB-P1-003 for evidence and RB-P1-007 for future repeatability requirements.
