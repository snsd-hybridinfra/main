# ZT-SYS-001 Rollback

Rollback is repository-only and must be reviewed. It is not performed during
normal validation.

1. Confirm the target diff contains only ZT-SYS-001 inventories, policies,
   schemas, validators, tests, package records, sanitized evidence, telemetry
   extensions, and tracking updates.
2. Preserve the existing OpenStack, EVE-NG, router, monitoring VM,
   Grafana/Loki/Alloy, restricted-validator, identity, network, endpoint,
   application, and data controls.
3. Revert package-owned files through a reviewed version-control change. Do
   not change target-local sudoers, SSH keys, generated Kolla configuration,
   router configuration, VM packages, or service state.
4. Do not automatically delete `.runtime/zero-trust/system/`. After evidence
   review, the operator may remove only exact run directories. Never use a
   broad or unresolved path.
5. Re-run the Zero Trust, synchronization, report, scenario-lock, secret, and
   runtime-ignore validations. Restore prior tracking language if the package
   authority is removed.

Rollback never restarts a service, restores a system, modifies a target
configuration, rotates a credential, changes a network path, or weakens an
existing restricted endpoint. Any such operation requires separate explicit
approval and an owner-controlled recovery procedure.
