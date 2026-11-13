# ZT-FND-001 Rollback

Rollback is a manual, reviewed operation and is not executed during normal validation. It must remove only package-specific access while preserving operator access and infrastructure configuration.

## Preconditions

1. Confirm an independent operator channel still works.
2. Identify only the dedicated validator aliases, accounts, keys, scripts, and sudoers entries.
3. Preserve OpenStack, EVE-NG, networking, services, and unrelated SSH material.
4. Capture a sanitized change record without private-key or credential content.

## Local rollback

- Remove only the `openstack-validator` and `eve-validator` SSH alias blocks if the package is being retired.
- Remove only the dedicated external validator key pairs after remote authorization entries have been removed.
- Delete only ignored `.runtime/zero-trust/` data selected by the operator.
- Preserve every unrelated SSH alias, key, `known_hosts` entry, and operator configuration.

## Remote rollback

For each host, through the preserved operator channel:

1. Disable only the `codex-validator` account or remove only its dedicated authorized-key line.
2. Remove only the package-specific sudoers entry after validating the remaining sudoers configuration.
3. Remove only the package-specific dispatcher and validator paths.
4. Do not remove shared packages or change OpenStack, EVE-NG, network, or service configuration.
5. Re-run safe access checks through the operator channel.

## Verification

- Dedicated validator login is rejected.
- Operator access remains available.
- No unrelated keys or accounts changed.
- No service, interface, route, security rule, VM, container, or lab node changed.
- Repository status is downgraded only after the rollback evidence authority is reviewed.

Never run this rollback solely to test that rollback works.
