# DNS Resolution Policy Example

NON-PRODUCTION EXAMPLE: this policy documents expected behavior without real domains, DNS servers, records, or resolver configuration.

## Hostname Naming Convention

- Host aliases use lowercase kebab-case names with a numeric suffix where multiple nodes may exist.
- Placeholder FQDNs combine the host alias with one approved symbolic domain suffix.

## Zone and Domain Separation Model

- Management and shared internal services use `<internal-domain>`.
- On-premises network devices use `<onprem-domain>`.
- AWS, Azure, OpenStack, and Kubernetes names use their provider-specific placeholder domains.
- Internal-only components have no dependency on public DNS.

## Resolution Rules

- Bastion and management hostname resolution rule: control-plane and bastion aliases resolve only within the approved management context.
- Database hostname resolution rule: application dependencies use `db-primary-01` or `db-replica-01` aliases, never embedded addresses.
- Kubernetes node hostname resolution rule: node aliases use `<kubernetes-domain-placeholder>`; service and ingress routing remain outside retired-numbered-case.
- Monitoring hostname resolution rule: monitoring, Prometheus, and Grafana aliases remain internal-only.
- Cloud service node hostname placeholder rule: provider nodes use `<aws-domain-placeholder>`, `<azure-domain-placeholder>`, or `<openstack-domain-placeholder>` without public DNS publication.

## Failure and Evidence

- Failure condition for unresolved hostnames: record `FAIL` or `BLOCKED` in the relevant future execution scenario; do not substitute an undocumented address.
- Evidence capture model: retain sanitized command references, validation judgment, and placeholder mapping without real resolver output in retired-numbered-case.

## Boundary

retired-numbered-case validates this repository model only. It does not query DNS, modify resolvers, connect to hosts, or authenticate to cloud providers.
