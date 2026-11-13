# ZT-ID-001 Bounded Identity Inventory, Role, Authentication, and Access Validation

## Package Identity

- Actions: `P1-ID-001`, `P1-ID-ENF-001-RETRY`
- Package: `ZT-ID-001`
- Type: `IDENTITY_VALIDATION`
- Phase: `PHASE_1`
- Policy version: `1.1.0`
- Authority: `AUTHORITATIVE`
- Package implementation: `IMPLEMENTED`
- Package validation: `RUNTIME_VALIDATED`
- Runtime validation: `VALIDATED`
- Runtime acceptance: `ACCEPTED`
- Runtime scope: `BOUNDED_NON_PRODUCTION_TARGET`
- Maturity: `UNASSESSED`

## Purpose

Implement a bounded identity-control model that validates
synthetic subject inventory, roles, authentication requirements, lifecycle
rules, deterministic authorization decisions, external secret references,
privacy controls, evidence, and recovery safeguards, and enforces a dedicated
least-privilege validator boundary on one non-production EVE-NG endpoint.

## Scope

The package contains JSON-compatible policy documents, JSON Schemas, a
read-only validator, synthetic fixtures, unit tests, sanitized local and
runtime evidence, package-owned forced-command and identity-summary helpers,
a validator-specific SSH boundary, and a least-privilege sudo allowlist.
Runtime acceptance is limited to the selected non-production endpoint.

## Explicit Exclusions

The package does not deploy or inspect Keycloak, LDAP, Active Directory,
MariaDB, Nginx, an OIDC provider, an MFA provider, PAM, an identity VM, or a
monitoring VM. It does not enumerate unrelated users, query OpenStack, rotate
credentials, or modify Grafana, Loki, Alloy, Docker Compose, ZT-VIS-002,
global sudoers content, third-party EVE-NG policy, or unrelated SSH settings.

It is not evidence that MFA, OIDC, runtime RBAC, federation, continuous
authentication, ICAM, biometric recognition, or a centralized identity service
is operational. It makes no Phase 1 completion or official maturity claim.

## Guideline Capability Mapping

| Capability | Canonical name | Bounded package relationship | Runtime state |
|---|---|---|---|
| `ZT-1.1.1` | 사용자 인벤토리 | Dedicated validator identity inventory and enforcement | `BOUNDED_RUNTIME_VALIDATED` |
| `ZT-1.1.2` | ID 연계 및 사용자 자격 증명 | Federation and credential-lifecycle requirement only | `NOT_VALIDATED` |
| `ZT-1.2.1` | 다중인증 (MFA) | Privileged-interactive MFA requirement only | `NOT_VALIDATED` |
| `ZT-1.4.1` | 조건부 사용자 접근 | Fixed operation allowlist and deterministic denial on the selected endpoint | `BOUNDED_RUNTIME_VALIDATED` |
| `ZT-1.4.2` | 최소 권한 접근 | Forced command, SSH restrictions, and exact sudo allowlist | `BOUNDED_RUNTIME_VALIDATED` |

`ZT-1.2.2`, `ZT-1.3.1`, and `ZT-1.3.2` remain excluded. `ZT-4.1.1`,
`ZT-4.2.1`, and `ZT-4.2.2` are related system-control references and are not
promoted by this package.

## Current Authority

The package YAML is authoritative for ZT-ID-001 package state. The capability
catalog remains authoritative for capability IDs and canonical Korean names.
Capability current assessment and maturity remain separate. The package records
only bounded runtime validation for the dedicated endpoint and assigns no
capability maturity.

Existing ZT-FND-001 evidence records dedicated forced-command validator
accounts and operator/validator key separation. That evidence is reused only as
a boundary reference; no account name, key, credential, or live inventory is
copied into ZT-ID-001.

## Identity Subject Model

The subject contract defines `HUMAN_OPERATOR`, `SERVICE_IDENTITY`,
`AUTOMATION_IDENTITY`, `VALIDATOR_IDENTITY`, and `BREAK_GLASS_IDENTITY`.
Every synthetic record includes identity ID and type, non-sensitive label,
owner role, accountable owner, target and environment scope, authentication
category, privilege, roles, lifecycle and approval state, creation authority,
review and expiration, revocation, sharing and interaction boundaries, MFA and
recovery requirements, evidence reference, and limitations.

## Role and Privilege Model

The bounded roles are `IDENTITY_READER`, `VALIDATION_OPERATOR`,
`EVIDENCE_REVIEWER`, `PACKAGE_APPROVER`, `MUTATING_OPERATOR`, and
`BREAK_GLASS_OPERATOR`. Each role defines allowed and prohibited actions,
approval requirements, interactive and mutating boundaries, evidence, runtime,
and secret access, and separation-of-duties conflicts.

Anonymous, unregistered, shared privileged, ownerless, unrestricted
administrator, unapproved privilege, read-only mutation, conflicting
validation/approval, and uncontrolled break-glass records are rejected.

## Authentication Assurance Model

The policy categories are `SSH_KEY`, `LOCAL_CREDENTIAL`, `FEDERATED_OIDC`,
`SERVICE_TOKEN`, `CERTIFICATE`, `MFA_PROTECTED_INTERACTIVE`, and
`BREAK_GLASS_CREDENTIAL`. Categories specify policy requirements only.

Privileged interactive and emergency identities require MFA in the target
model and record `REQUIRED_NOT_IMPLEMENTED`. Automation, service, and validator
identities are non-interactive and use external secret references. No category
is treated as deployed by this package.

## Lifecycle Model

The lifecycle states are `PROPOSED`, `APPROVED`, `ACTIVE`, `SUSPENDED`,
`REVOKED`, `EXPIRED`, and `REVIEW_REQUIRED`. Active records require an owner and
approval. Revoked records cannot retain roles; expired and suspended records
cannot receive positive authorization. Review-due behavior is privilege-aware,
and emergency identities require explicit expiration.

## Decision Model

The decisions are `ALLOW`, `DENY`, `REVIEW_REQUIRED`, and `NOT_APPLICABLE`.
Every decision contains a stable decision ID, identity, action, target, role,
policy version, reason codes, approval requirement, evidence authority, fixture
time, and limitations. The default policy is
`DENY_BY_DEFAULT_FOR_UNREGISTERED_IDENTITY`.

An `ALLOW` result applies only to a synthetic policy evaluation and never
grants live access.

## Positive Acceptance Cases

Nine positive cases cover a read-only human, validation operator, evidence
reviewer, scoped automation identity, non-interactive validator, controlled
break-glass design, approved mutating fixture, future OIDC requirement marked
not implemented, and non-interactive service identity.

## Negative Acceptance Cases

Thirty-four negative cases cover missing or duplicate IDs, unknown types,
missing owners, shared privilege, missing MFA requirement, expiry, revocation,
suspension, unregistered access, read-only mutation, interactive automation,
invalid service scope, incomplete break-glass controls, synthetic secret-field
injection, separation conflicts, invalid role/lifecycle/authentication values,
fictional deployment and maturity claims, successor numbered scenario and runtime tracking, production
data markers, missing approval, and unrestricted emergency scope.

Controlled secret-field names and synthetic sentinel values exist only in the
negative fixture set to prove rejection. They are not credentials.

## Evidence Contract

The retained local record is
`docs/evidence/zero-trust/zt-id-001-local-validation.yaml`. Runtime acceptance
is recorded in `docs/evidence/zero-trust/zt-id-001-runtime-validation.yaml`
under `USER_APPROVED_CODEX_EXECUTION` and
`BOUNDED_NON_PRODUCTION_ENFORCEMENT`. It records sanitized control outcomes,
20 positive passes, 42 deterministic denials, zero unexpected allowances,
explicit limitations, and no raw authentication data.

## Privacy and Data-Minimization Boundary

The package enforces purpose limitation, minimum fields, synthetic fixtures,
non-sensitive target labels, and sanitized evidence. It prohibits personal
email, full names, production account exports, password hashes, authentication
factors, and complete login histories. The retention policy keeps only reviewed
synthetic artifacts and sanitized counts.

## Secret Boundary

Only `env://`, `file-ref://`, `vault-ref://`, and `external-secret://` logical
references are accepted. The validator never dereferences them. Passwords,
tokens, client secrets, private keys, MFA seeds, recovery codes, `clouds.yaml`,
`passwords.yml`, and real environment contents are prohibited.

## Lockout Prevention

Live enforcement requires a non-production target, confirmed break-glass path,
tested recovery, known-good administrative session, bounded roles, session
timeout, rollback owner, prior-policy backup, and an immediate stop on
unexpected denial. Bulk disablement, initial factor rotation, production use,
and removal of the default administrative role are prohibited.

P1-ID-ENF-001-RETRY met these gates with two operator sessions, an independent
VMware console, target-local backups, and an armed automatic rollback timer.

## Break-Glass Requirements

The emergency design record must be non-shared, owner-bound, approved,
time-limited, externally referenced, logged, recoverable, rollback-capable, and
scope-bounded. The runtime action exercised the independent recovery-console
path without creating, exposing, or changing an emergency credential.

## Failure Handling

Local failures retain the synthetic failing input and reason code. They do not
authorize a weaker rule or runtime workaround. Any unexpected live
denial requires an immediate stop, preservation of the known-good session,
approved recovery, policy restoration, and revalidation.

## Rollback

The runtime action captured every package-owned file and relevant account,
group, SSH, sudo, and identity-database state before enforcement. An idempotent
target-local rollback was armed before access-control changes, refreshed during
testing, and cancelled only after evidence and all safety checks passed. No
rollback timer or job remains.

## Runtime Validation Boundary

Runtime validation covers one reused dedicated account and group, a
package-owned forced-command dispatcher, a read-only identity helper, exact
sudo commands, public-key-only SSH, and denial of interactive shell, PTY,
SCP/SFTP, forwarding, alternate executables, and arbitrary commands. It does
not validate OpenStack identity, Keycloak, Grafana OIDC roles, certificates, or
production identities.

## Phase 2 Dependency Boundary

Centralized identity, Keycloak, federation, MFA enforcement, OIDC, runtime RBAC,
application integration, access-decision telemetry, and ZT-ID-002 remain Phase
2 or separately approved work. ZT-VIS-002 is protected and is neither identity
evidence nor a prerequisite modified by this action.

## Known Limitations

- Enterprise identity inventory remains absent; only the dedicated validator
  identity on one target was inspected.
- Runtime decisions are limited to a fixed forced-command allowlist and are not
  a centralized or adaptive policy enforcement point.
- MFA and OIDC are requirements, not operating controls.
- Application RBAC and centralized identity lifecycle remain absent.
- Production identity enforcement is not validated.
- Capability maturity remains `UNASSESSED`.
- Phase 1 is `PARTIAL`, `PARTIALLY_VALIDATED`, and `COMPLETED_WITH_GAPS` under the scoped RV freshness exception; this package does not close that residual risk.

## Package Acceptance

Package acceptance requires all schemas to parse, all models to satisfy schema
and semantic rules, nine positive cases to match expected decisions,
thirty-three negative cases to be rejected for the expected reason, evidence to
synchronize, the validator and unit tests to pass, retired numbered scenario framework to remain locked,
successor numbered scenario to remain absent, and no secret or runtime file to be tracked.

Runtime acceptance additionally requires at least 20 positive checks, 42
harmless deterministic denials, zero unexpected allowances, preserved operator
and console recovery, valid SSH and sudoers configuration, unchanged
third-party policy, generated sanitized evidence, and no residual rollback job.

Acceptance sets ZT-ID-001 to `PRESENT`, `IMPLEMENTED`, and
`RUNTIME_VALIDATED`; runtime validation is `VALIDATED`, runtime acceptance is
`ACCEPTED`, scope is `BOUNDED_NON_PRODUCTION_TARGET`, and maturity stays
`UNASSESSED`.

## Related Runbooks

- `docs/runbooks/phase-1/06-identity-validation-readiness.md`
- `docs/runbooks/phase-1/03-evidence-handling-and-sanitization.md`
- `docs/runbooks/phase-1/07-repeatable-and-scheduled-validation.md`

## Related Architecture

- `docs/zero-trust/target-architecture/implementation-dependency-map.md`
- `docs/zero-trust/target-architecture/operator-interface-contract.md`
- `docs/zero-trust/target-architecture/security-boundaries.md`
