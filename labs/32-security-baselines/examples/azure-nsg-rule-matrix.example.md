# Azure NSG Rule Matrix Example

NON-PRODUCTION EXAMPLE: these rows are policy placeholders and do not create Azure rules.

| NSG | Direction | Protocol | Port | Source/Destination | Priority Placeholder | Purpose | Public Exposure | Least Privilege Judgment | Evidence Reference |
|---|---|---|---:|---|---|---|---|---|---|
| azure-public-web-nsg | inbound | tcp | 80 | Internet | `<priority-public-http>` | Public HTTP for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| azure-public-web-nsg | inbound | tcp | 443 | Internet | `<priority-public-https>` | Public HTTPS for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| azure-bastion-nsg | inbound | tcp | 22 | `<management-cidr>` | `<priority-management-ssh>` | Administrative SSH from approved management source | no | PASS | retired-numbered-case |
| azure-bastion-nsg | inbound | tcp | 3389 | `<management-cidr>` | `<priority-management-rdp>` | RDP placeholder restricted to approved management source | no | PASS | retired-numbered-case |
| azure-private-service-nsg | inbound | tcp | `<internal-service-port>` | `<public-web-nsg>` | `<priority-internal-service>` | Public tier to private service tier | no | PASS | retired-numbered-case |
| azure-database-nsg | inbound | tcp | 3306 | `<private-service-nsg>` | `<priority-mariadb>` | MariaDB from private service NSG | no | PASS | retired-numbered-case |
| azure-database-nsg | inbound | tcp | 5432 | `<private-service-nsg>` | `<priority-postgresql>` | PostgreSQL from private service NSG | no | PASS | retired-numbered-case |
| azure-database-nsg | inbound | tcp | 6379 | `<private-service-nsg>` | `<priority-redis>` | Redis from private service NSG | no | PASS | retired-numbered-case |
| azure-monitoring-nsg | inbound | tcp | 9200 | `<private-service-nsg>` | `<priority-metrics>` | Metrics/search placeholder from private service tier | no | PASS | retired-numbered-case |
| azure-monitoring-nsg | inbound | tcp | 5601 | `<management-cidr>` | `<priority-dashboard>` | Dashboard placeholder from management source | no | PASS | retired-numbered-case |
| azure-monitoring-nsg | inbound | tcp | 9090 | `<management-cidr>` | `<priority-prometheus>` | Prometheus placeholder from management source | no | PASS | retired-numbered-case |
| azure-monitoring-nsg | inbound | tcp | 3000 | `<management-cidr>` | `<priority-grafana>` | Grafana placeholder from management source | no | PASS | retired-numbered-case |
| azure-private-service-nsg | outbound | tcp | 443 | Internet | `<priority-justified-egress>` | Justified HTTPS update path placeholder | egress-only | REVIEW_REQUIRED | retired-numbered-case |

## Required Denial Expectations

- SSH 22 must not allow `0.0.0.0/0` or `Internet`.
- RDP 3389 must not allow `0.0.0.0/0` or `Internet`.
- MySQL/MariaDB 3306 must not allow `0.0.0.0/0` or `Internet`.
- PostgreSQL 5432 must not allow `0.0.0.0/0` or `Internet`.
- Redis 6379 must not allow `0.0.0.0/0` or `Internet`.
- HTTP 80 and HTTPS 443 may use `0.0.0.0/0` or `Internet` only on `azure-public-web-nsg` for the public web tier placeholder.
- Internal service ports must use a private CIDR, subnet, or NSG reference placeholder.
