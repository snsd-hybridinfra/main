# SSH Root Login Denial Baseline

This document defines a non-production repository baseline. It contains no real user, root password, key, host, or deployable SSH server configuration.

## Required Controls

- `PermitRootLogin` must be set to `no`.
- Direct root SSH login is denied for `<bastion-host>` and `<target-host>`.
- Administrative login must use the approved non-root administrative user placeholder `<admin-user>`.
- Privilege escalation must be controlled through the approved sudo policy placeholder `<sudo-policy-path>` and `<approved-privilege-escalation-process>`.
- Root password must never be stored in the repository.
- SSH key authentication remains the approved administrative login method.
- Password authentication denial remains required.
- SSH configuration reference: `<ssh-config-path>`.

## Evidence Collection Model

- Record repository directive, policy, root-password safety, private-key safety, and execution-boundary results at `<evidence-path>` through the retired-numbered-case generated evidence.
- Do not capture usernames, root-login attempts, passwords, keys, credentials, private paths, or live authentication output.
- Key authentication and password-login denial remain in retired-numbered-case and retired-numbered-case.
