# Lab 32: Zero Trust Security Control Baselines

**Status:** `REFERENCE_MIGRATED / NOT_REVALIDATED`. Curated rules, templates, control patterns, and policy schemas; no enforcement or certification claim.

## Scope
- `examples/`: MariaDB, Nginx, SSH, security groups, Grafana access and misconfiguration/rollback examples
- `policies/`: source identity, data protection, service baseline, secure deployment and IaC/CaC/PaC reference design
- Reuse links: [Lab 17](../17-cloud-network-access-baselines/README.md) (OpenStack/K8s), [Lab 24](../24-multicloud-network-iac/README.md) (AWS/Azure), [Lab 21](../21-automation-approval/README.md) (changes)

## Important distinction
Original Zero Trust architecture included many package histories, risk assessments, evidence manifests, version-specific validations and implementation plans; this lab extracts **reusable policy patterns only**, not a certified/production Zero Trust implementation. Labels must never imply real-world compliance.

## Lab tasks
1. Convert placeholder references into explicit synthetic assets and default-deny rule cases.
2. Implement unit assertions for correct deny/pass of SSH, database, service/API and cloud network access.
3. Add change approval / rollback and retained evidence to validate policy enforcement.
4. Document accepted exceptions and review intervals. No changes to live systems.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. Historical governance and raw validation evidence remain in the source repository until independently backed up.
