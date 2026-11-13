# OpenStack Security Group Baseline

This document defines a repository-side, non-production policy model. It does not create or query OpenStack resources.

## Inbound Policy

- Default deny inbound principle: traffic is denied unless a documented rule explicitly allows it.
- Explicit allow only for required service ports, protocols, sources, and tiers.
- SSH access is allowed only from `<management-cidr>` or `<bastion-security-group>`.
- No public SSH from `0.0.0.0/0` is permitted.
- No public database access from `0.0.0.0/0` is permitted.
- No public monitoring/admin access from `0.0.0.0/0` is permitted.
- HTTP/HTTPS public exposure is allowed only for `<public-web-security-group>` in the public service tier placeholder.
- Internal service access must use a private CIDR or security group reference placeholder within `<openstack-private-network-cidr>`.
- Private application traffic belongs to `<private-service-security-group>`.
- Database traffic must terminate at `<database-security-group>` and monitoring traffic at `<monitoring-security-group>`.

## Egress Policy

Egress must be documented and justified. A broad egress destination requires a named purpose, review judgment, and evidence reference.

## Terraform Boundary

The existing `openstack_networking_secgroup_v2` and management-scoped `openstack_networking_secgroup_rule_v2` resources are safe structural placeholders. retired-numbered-case does not add broad rules or run Terraform.

## Evidence Collection Model

- Run the local validator without OpenStack authentication or network access.
- Store the generated log and summary below `<evidence-path>`.
- Record every check by stable check ID.
- Reject credentials, identity values, state, real variables, public addresses, and secret material.
