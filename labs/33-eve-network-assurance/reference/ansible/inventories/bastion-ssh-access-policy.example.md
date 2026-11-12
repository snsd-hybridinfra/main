# Bastion SSH Access Policy Example

NON-PRODUCTION EXAMPLE: this policy defines expected control statements without usernames, addresses, keys, credentials, or executable SSH configuration.

## Administrative Access Model

- Bastion-only administrative access model: administrative traffic must follow `control-plane-01 -> bastion-host-01 -> <allowed-target-group>`.
- Management source placeholder: `<management-source-cidr>`.
- Allowed target groups placeholder: `<internal-server-group>`, `<monitoring-group>`, `<database-group>`, `<kubernetes-node-group>`, `<network-device-group>`, and `<cloud-service-node-group>`.
- Denied direct access paths placeholder: `<public-source> -> <internal-target>` and `<unapproved-source> -> bastion-host-01`.

## Required SSH Controls

- No direct public SSH to internal servers.
- SSH key authentication required.
- Password login denied.
- Root login denied.
- Private key paths and authorized key contents must remain outside the repository.

## Validation Boundary

retired-numbered-case verifies that these statements exist. Enforcement and live authentication are validated separately in retired-numbered-case, retired-numbered-case, and retired-numbered-case. Network least-privilege controls are validated in retired-numbered-case, retired-numbered-case, and retired-numbered-case.
