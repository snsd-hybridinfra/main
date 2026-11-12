# SSH Key Authentication Baseline

This document defines a non-production repository baseline. It is not a live SSH server configuration and contains no user-bound key material.

## Required Controls

- SSH key authentication required for administrative access.
- Password authentication disabled reference: `PasswordAuthentication no`.
- Root login disabled reference: `PermitRootLogin no`.
- Bastion-only administrative access reference: `<admin-user> -> <bastion-host> -> <target-host>`.
- Public key placement rule placeholder: place `<public-key-placeholder>` only through an approved external process at `<authorized-keys-path>`.
- Private key storage rule: never commit private keys to this repository.
- Key rotation placeholder: `<key-rotation-procedure>` must replace retired public-key authorization through a separately approved process.
- Authorized user placeholder model: `<admin-user>` represents an approved administrative identity; no real username belongs in the repository.
- SSH configuration path placeholder: `<ssh-config-path>`.

## Evidence Collection Model

- Record repository-baseline checks in the retired-numbered-case generated log and summary.
- Do not capture key contents, usernames, passwords, private paths, or live authentication output.
- Live enforcement for password and root login denial remains in retired-numbered-case and retired-numbered-case.
