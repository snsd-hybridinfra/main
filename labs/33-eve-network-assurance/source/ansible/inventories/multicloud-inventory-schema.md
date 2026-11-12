# Multi-Cloud Inventory Schema

This schema describes the non-production repository inventory used by retired-numbered-case. It does not describe live host discovery or authentication.

## Required Fields

| Field | Purpose |
|---|---|
| `inventory_group` | Group containing the host alias. Represented by the YAML group key. |
| `host_alias` | Stable placeholder hostname used by documentation and evidence. |
| `provider_or_zone` | Provider or on-premises placement classification. |
| `component_type` | Functional component classification. |
| `environment` | Must identify the entry as a non-production example. |
| `management_path_placeholder` | Symbolic management route; never a real path, key, or endpoint. |
| `validation_scope` | Declares repository-only validation. |
| `evidence_reference` | Scenario evidence reference, such as `retired-numbered-case`. |

`ansible_host` is required in the example inventory and must remain an angle-bracket placeholder such as `<aws-service-node-ip>`.

## Allowed `provider_or_zone` Values

- `on-prem`
- `aws`
- `azure`
- `openstack`
- `control-plane`

## Allowed `component_type` Values

- `bastion`
- `network`
- `compute`
- `kubernetes`
- `database`
- `monitoring`
- `service`

## Safety Rules

- Do not store real IP addresses, instance identifiers, account identifiers, usernames, credentials, key paths, tokens, vault values, or private paths.
- Do not create a live or production inventory in this repository.
- Host existence, reachability, DNS resolution, and cloud resource discovery are outside retired-numbered-case.
