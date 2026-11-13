# OpenStack Security Group Rule Matrix Example

NON-PRODUCTION EXAMPLE: these rows are policy placeholders and do not create OpenStack rules.

| Security Group | Direction | Ethertype | Protocol | Port Range | Remote IP Prefix / Remote Group | Purpose | Public Exposure | Least Privilege Judgment | Evidence Reference |
|---|---|---|---|---:|---|---|---|---|---|
| openstack-public-web-sg | ingress | IPv4 | tcp | 80 | 0.0.0.0/0 | Public HTTP for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| openstack-public-web-sg | ingress | IPv4 | tcp | 443 | 0.0.0.0/0 | Public HTTPS for public web tier placeholder | yes-public-web-only | PASS | retired-numbered-case |
| openstack-bastion-sg | ingress | IPv4 | tcp | 22 | `<management-cidr>` | Administrative SSH from approved management source | no | PASS | retired-numbered-case |
| openstack-private-service-sg | ingress | IPv4 | tcp | `<internal-service-port>` | `<public-web-security-group>` | Public tier to private service tier | no | PASS | retired-numbered-case |
| openstack-database-sg | ingress | IPv4 | tcp | 3306 | `<private-service-security-group>` | MariaDB from private service group | no | PASS | retired-numbered-case |
| openstack-database-sg | ingress | IPv4 | tcp | 5432 | `<private-service-security-group>` | PostgreSQL from private service group | no | PASS | retired-numbered-case |
| openstack-database-sg | ingress | IPv4 | tcp | 6379 | `<private-service-security-group>` | Redis from private service group | no | PASS | retired-numbered-case |
| openstack-monitoring-sg | ingress | IPv4 | tcp | 9200 | `<private-service-security-group>` | OpenSearch/Elasticsearch placeholder | no | PASS | retired-numbered-case |
| openstack-monitoring-sg | ingress | IPv4 | tcp | 5601 | `<management-cidr>` | Kibana/OpenSearch Dashboards placeholder | no | PASS | retired-numbered-case |
| openstack-monitoring-sg | ingress | IPv4 | tcp | 9090 | `<management-cidr>` | Prometheus placeholder | no | PASS | retired-numbered-case |
| openstack-monitoring-sg | ingress | IPv4 | tcp | 3000 | `<management-cidr>` | Grafana placeholder | no | PASS | retired-numbered-case |
| openstack-private-service-sg | egress | IPv4 | tcp | 443 | 0.0.0.0/0 | Justified HTTPS update path placeholder | egress-only | REVIEW_REQUIRED | retired-numbered-case |

## Required Denial Expectations

- SSH 22 must not allow `0.0.0.0/0`.
- MySQL/MariaDB 3306 must not allow `0.0.0.0/0`.
- PostgreSQL 5432 must not allow `0.0.0.0/0`.
- Redis 6379 must not allow `0.0.0.0/0`.
- Prometheus 9090 must not allow `0.0.0.0/0`.
- Grafana 3000 must not allow `0.0.0.0/0`.
- OpenSearch/Elasticsearch 9200 must not allow `0.0.0.0/0`.
- Kibana/OpenSearch Dashboards 5601 must not allow `0.0.0.0/0`.
- HTTP 80 and HTTPS 443 may use `0.0.0.0/0` only on `openstack-public-web-sg` for the public web tier placeholder.
- Internal service ports must use a private CIDR or security group reference placeholder.
