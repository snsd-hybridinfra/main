# Lab 44: OpenStack Monitoring VM + mTLS Deployment Reference

**Status:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. Copied **37 source files** containing Ansible monitoring roles, OpenStack Terraform modules/environment, constrained validation playbooks and policy contracts.

## Question
Can an isolated OpenStack monitoring node be provisioned with least-privilege, local Grafana/Loki/Alloy/Prometheus/Blackbox endpoints and a tightly controlled mTLS/NGINX ingress, while making restarts and rollback separately authorized?

## Structure
- `reference/terraform/`: monitoring VM, dedicated port, data volume and isolated environment
- `reference/ansible/roles/`: host bootstrap + container monitoring stack roles
- `reference/ansible/playbooks/`: deploy, bootstrap, alert validation, rollback and live validation **reference sources**
- `reference/docs/`: source readiness/deployment contracts

## Safety and next tests
- Some roles may modify partition/volume content, host firewall, packages, nginx, network listeners and running monitoring containers. **Do not run directly.** Review all tasks, destructive volume handling, idempotency, previous checkpoints and the credentials boundary.
- The source defaults require reviewed authorizations (generally false by default), but that alone does not prove safety.
- First validate YAML/Terraform statically and mock external actions. Only in a disposable, non-routable tenant should deployment, denial, mTLS auth failure, storage persistence and rollback be tested.
- Images are historical digest pins; independently verify registry availability and security posture.
- This lab is distinct from [Lab 18](../18-sanitized-observability/README.md), which focuses on a bounded Docker Compose logging stack.

**Provenance:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No live cloud actions performed.
