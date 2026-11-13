# Azure NSG Least Privilege Baseline

This document defines a repository-side, non-production policy model. It does not create or query Azure resources.

## Inbound Policy

- Default deny inbound principle: traffic is denied unless a documented rule explicitly allows it.
- Explicit allow only for required service ports, sources, destinations, and tiers.
- SSH access is allowed only from `<management-cidr>` or `<bastion-subnet-cidr>`.
- No public SSH from `0.0.0.0/0` or `Internet` is permitted.
- No public RDP from `0.0.0.0/0` or `Internet` is permitted.
- No public database access from `0.0.0.0/0` or `Internet` is permitted.
- HTTP/HTTPS public exposure is allowed only for `<public-web-nsg>` in the public service tier placeholder.
- Internal service access must use a private CIDR, subnet, or NSG reference placeholder within `<azure-vnet-cidr>`.
- Database traffic must terminate at `<database-nsg>` and monitoring traffic at `<monitoring-nsg>`.
- Private application traffic belongs to `<private-service-nsg>`.

## Egress Policy

Egress must be documented and justified. A broad egress destination is not implicit approval; it requires a named purpose, review judgment, and evidence reference.

## Terraform Boundary

The existing `azurerm_network_security_group` and `azurerm_subnet_network_security_group_association` resources are safe structural placeholders. An `azurerm_network_security_rule` is documented as a future implementation placeholder only; standalone-lab does not add or apply deployable rules.

## Evidence Collection Model

- Run the local validator without Azure authentication or network access.
- Store the generated log and summary below `<evidence-path>`.
- Record every check by stable check ID.
- Reject real credentials, identity values, state, variable values, public addresses, and secret material.
