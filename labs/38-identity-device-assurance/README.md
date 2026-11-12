# Lab 38: Identity & Device Assurance Controls

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. Extracted 8 identity and 4 device policy files. These are policy examples, not an operational IAM / EDR / NAC deployment.

## Main concerns
- Subject identity and authentication assurance model, role-to-policy matrix, lifecycle and revocation
- Fail-closed identity decision rules and rollback/lockout risk
- Device inventory, endpoint compliance gates and vulnerability assessment plan

## Independent tests to implement
1. Authorized and unauthorized role actions, expired/disabled identities, MFA/session expiry and deny by default.
2. Missing/unknown endpoint trust, stale posture, unmanaged device and exception expiry.
3. Model the risks of account lockout and test rollback without creating a production access outage.
4. Use synthetic identities, fake device records and time-fixed fixtures only.

## Integration possibilities
Lab 28 (approval/grant) and Lab 32 (security baselines). These must remain separate until access-denial behavior is actually verified in a disposable environment.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
