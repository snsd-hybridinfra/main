# ZT-ID-001 Rollback and Lockout Safety

## Current boundary

P1-ID-001 established the local policy package. P1-ID-ENF-001-RETRY then
normalized the existing package-owned validator identity boundary on one
approved non-production EVE-NG endpoint. The account and group were reused;
the action changed only package-owned wrapper, helper, SSH, authorized-key,
sudoers, and ownership metadata. It did not change credentials, authentication
factors, global sudoers, third-party EVE-NG policy, or an identity provider.

## Mandatory live-enforcement safeguards

The runtime action applied all of the following mandatory safeguards:

1. Use an explicitly approved non-production target.
2. Confirm a separately controlled break-glass path.
3. Document and test the recovery path before enforcement.
4. Preserve a known-good administrative session.
5. Bound every role and target scope.
6. Define a session timeout and credential expiry.
7. Identify the rollback owner and accountable approver.
8. Back up the prior policy without copying secrets into Git.
9. Stop immediately on any unexpected denial or administrative-path loss.
10. Prohibit bulk account disablement.
11. Prohibit password, key, token, or factor rotation during initial validation.
12. Exclude production targets.
13. Preserve the default administrative role until recovery is proven.
14. Require explicit user approval before live enforcement.

The validator rejects a runtime record that lacks recovery, backup, automatic
rollback, operator access, complete deny-test, or limitation evidence. The
local policy validator also rejects a future runtime plan that lacks a break-glass
identity, rollback procedure, recovery procedure, lockout stop condition, or
accountable approver.

The accepted target-local backup records file existence, checksums, metadata,
account and group state, effective SSH and sudo scope, identity-database state,
and protected third-party checksums. The idempotent rollback restores existing
files atomically, removes action-created files, validates SSH and sudoers before
reload, and preserves unrelated files. Its one-time systemd timer was armed
before enforcement, refreshed during testing, and cancelled after acceptance;
residual timers and jobs are zero.

## Failure handling

If a local fixture or policy validation fails, make no runtime change. Record
the reason code, preserve the failing synthetic input, repair only the package
model or validator, and rerun the targeted tests. A schema or validator failure
does not authorize a weaker rule.

If a live action causes an unexpected denial, stop the action, keep the
known-good administrative session open, use the approved recovery path, restore
the prior policy, and revalidate the original access path before proceeding.

P1-ID-ENF-001-RETRY observed no unexpected allowance or administrative-path
loss. Two new operator sessions, the independent VMware console, SSH service,
global and package sudoers, and the protected EVE-NG sudoers file all passed
their final checks before rollback cancellation.

## Break-glass requirements

A break-glass design record requires a non-shared identity, accountable owner,
explicit approval, expiration, external secret reference, logging requirement,
recovery procedure, rollback procedure, and lockout stop condition. The runtime
action verified the independent VMware recovery path without creating,
changing, or exposing a break-glass credential.

## Phase 2 boundary

Keycloak, LDAP, Active Directory, OIDC, MFA enforcement, application RBAC,
centralized identity lifecycle, PAM, and access-decision telemetry are Phase 2
or separately approved runtime work. They are not rollback targets of this
bounded endpoint package and remain absent after runtime acceptance.
