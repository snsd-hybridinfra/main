# SSH Password Login Denial Baseline

This document defines a non-production repository baseline. It contains no real user, password, key, host, or deployable SSH server configuration.

## Required Controls

- `PasswordAuthentication` must be set to `no`.
- `ChallengeResponseAuthentication` must be set to `no`.
- `KbdInteractiveAuthentication` must be set to `no`.
- SSH key authentication remains the approved administrative login method.
- Password login is denied for `<bastion-host>` and `<target-host>`.
- No password values are stored in inventory or repository files.
- Emergency access is handled outside this repository through `<approved-break-glass-process>` and an approved operational process.

## Placeholder Model

- Authorized administrative identity: `<admin-user>`
- Bastion target: `<bastion-host>`
- Internal target: `<target-host>`
- SSH configuration reference: `<ssh-config-path>`
- Evidence destination: `<evidence-path>`

## Evidence Collection Model

- Record repository directive, policy, password-value safety, private-key safety, and execution-boundary results in the retired-numbered-case generated log and summary.
- Do not capture usernames, password attempts, credentials, private paths, keys, or live authentication output.
- SSH key authentication is validated separately in retired-numbered-case; root-login denial remains in retired-numbered-case.
