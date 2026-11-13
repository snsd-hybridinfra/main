# Hostname Resolution Map Example

NON-PRODUCTION EXAMPLE: these records are symbolic documentation only and are not real public or private DNS records.

## Placeholder Mappings

| Host Alias | Placeholder FQDN | Address Placeholder | Zone Classification |
|---|---|---|---|
| `control-plane-01` | `control-plane-01.<internal-domain>` | `<control-plane-ip>` | management |
| `bastion-host-01` | `bastion-host-01.<internal-domain>` | `<bastion-host-ip>` | management |
| `onprem-router-placeholder` | `onprem-router-placeholder.<onprem-domain>` | `<onprem-router-ip>` | on-prem network |
| `aws-service-node-01` | `aws-service-node-01.<aws-domain-placeholder>` | `<aws-service-node-ip>` | AWS service |
| `azure-service-node-01` | `azure-service-node-01.<azure-domain-placeholder>` | `<azure-service-node-ip>` | Azure service |
| `openstack-service-node-01` | `openstack-service-node-01.<openstack-domain-placeholder>` | `<openstack-service-node-ip>` | OpenStack service |
| `k8s-node-01` | `k8s-node-01.<kubernetes-domain-placeholder>` | `<k8s-node-ip>` | Kubernetes node |
| `db-primary-01` | `db-primary-01.<internal-domain>` | `<db-primary-ip>` | database |
| `db-replica-01` | `db-replica-01.<internal-domain>` | `<db-replica-ip>` | database |
| `monitoring-node-01` | `monitoring-node-01.<internal-domain>` | `<monitoring-node-ip>` | monitoring |
| `prometheus-placeholder` | `prometheus-placeholder.<internal-domain>` | `<monitoring-node-ip>` | monitoring service |
| `grafana-placeholder` | `grafana-placeholder.<internal-domain>` | `<monitoring-node-ip>` | monitoring service |

## Resolution Boundary

The map defines names and placement only. It does not create DNS zones, hosts-file entries, resolver configuration, public records, or evidence that any name resolves.
