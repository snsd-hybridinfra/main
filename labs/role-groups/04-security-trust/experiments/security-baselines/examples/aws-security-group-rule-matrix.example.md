# AWS Security Group Rule Matrix Example

NON-PRODUCTION EXAMPLE: these rows are policy placeholders and do not create AWS rules.

| Security Group | Direction | Protocol | Port | Source/Destination | Purpose | Public Exposure | Least Privilege Judgment | Evidence Reference |
|---|---|---|---:|---|---|---|---|---|
| aws-public-web-sg | ingress | tcp | 80 | 0.0.0.0/0 | Public HTTP for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| aws-public-web-sg | ingress | tcp | 443 | 0.0.0.0/0 | Public HTTPS for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| aws-bastion-sg | ingress | tcp | 22 | `<management-cidr>` | Administrative SSH from approved management source | no | PASS | retired-numbered-case |
| aws-bastion-sg | ingress | tcp | 3389 | `<management-cidr>` | RDP placeholder restricted to approved management source | no | PASS | retired-numbered-case |
| aws-private-service-sg | ingress | tcp | `<internal-service-port>` | `<public-web-security-group>` | Public tier to private service tier | no | PASS | retired-numbered-case |
| aws-database-sg | ingress | tcp | 3306 | `<private-service-security-group>` | MariaDB access from private service tier | no | PASS | retired-numbered-case |
| aws-database-sg | ingress | tcp | 5432 | `<private-service-security-group>` | PostgreSQL placeholder from private service tier | no | PASS | retired-numbered-case |
| aws-database-sg | ingress | tcp | 6379 | `<private-service-security-group>` | Redis placeholder from private service tier | no | PASS | retired-numbered-case |
| aws-monitoring-sg | ingress | tcp | 9200 | `<private-service-security-group>` | Metrics/search placeholder from private service tier | no | PASS | retired-numbered-case |
| aws-monitoring-sg | ingress | tcp | 5601 | `<management-cidr>` | Dashboard placeholder from management source | no | PASS | retired-numbered-case |
| aws-monitoring-sg | ingress | tcp | 9090 | `<management-cidr>` | Prometheus placeholder from management source | no | PASS | retired-numbered-case |
| aws-monitoring-sg | ingress | tcp | 3000 | `<management-cidr>` | Grafana placeholder from management source | no | PASS | retired-numbered-case |
| aws-private-service-sg | egress | tcp | 443 | 0.0.0.0/0 | Justified HTTPS update path placeholder | egress-only | REVIEW_REQUIRED | retired-numbered-case |

## Required Denial Expectations

- SSH 22 must not allow `0.0.0.0/0`.
- RDP 3389 must not allow `0.0.0.0/0`.
- MySQL/MariaDB 3306 must not allow `0.0.0.0/0`.
- PostgreSQL 5432 must not allow `0.0.0.0/0`.
- Redis 6379 must not allow `0.0.0.0/0`.
- HTTP 80 and HTTPS 443 may use `0.0.0.0/0` only on `aws-public-web-sg` for the public web tier placeholder.
- Internal service ports must use a private CIDR or security-group reference placeholder.
