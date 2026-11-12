# Bastion Reachability Map Example

NON-PRODUCTION EXAMPLE: this file defines symbolic access paths only. It does not assert that any host, route, or address exists.

## Required Access Paths

| Source | Path | Target or Zone | Address Placeholder | Purpose |
|---|---|---|---|---|
| `control-plane-01` | `control-plane-01 -> bastion-host-01` | `bastion-host-01` | `<bastion-host-ip>` | Administrative entry path |
| `bastion-host-01` | `bastion-host-01 -> internal-server-zone` | `internal-server-zone` | `<internal-server-cidr>` | Internal service administration |
| `bastion-host-01` | `bastion-host-01 -> monitoring-zone` | `monitoring-zone` | `<monitoring-cidr>` | Monitoring administration |
| `bastion-host-01` | `bastion-host-01 -> database-nodes` | `db-primary-01`, `db-replica-01` | `<database-cidr>` | Database node administration |
| `bastion-host-01` | `bastion-host-01 -> kubernetes-nodes` | `k8s-node-01` | `<kubernetes-node-cidr>` | Kubernetes node administration |
| `bastion-host-01` | `bastion-host-01 -> on-prem-network-devices placeholder` | `onprem-router-placeholder` | `<internal-server-cidr>` | On-premises network-device path model |
| `bastion-host-01` | `bastion-host-01 -> cloud-service-nodes placeholder` | `aws-service-node-01`, `azure-service-node-01`, `openstack-service-node-01` | provider-specific placeholders | Cloud service-node path model |

## Required Target Placeholders

- `bastion-host-01`: `<bastion-host-ip>`
- `db-primary-01`: `<database-cidr>`
- `db-replica-01`: `<database-cidr>`
- `monitoring-node-01`: `<monitoring-cidr>`
- `k8s-node-01`: `<kubernetes-node-cidr>`
- `aws-service-node-01`: `<aws-service-node-ip>`
- `azure-service-node-01`: `<azure-service-node-ip>`
- `openstack-service-node-01`: `<openstack-service-node-ip>`

## Boundary

This map is consumed only by repository validation. Reachability, route state, DNS, SSH, security-group rules, and real instance existence are not tested here.
