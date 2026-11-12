# Lab 17: Cloud Network and Access Guardrails

**Status:** `MIGRATED / NOT_REVALIDATED`. Selected reusable infrastructure and access-control baselines extracted from a larger retired experimentation repo; no runtime claim.

## Question
Can a private OpenStack subnet, routing boundary and restricted management security group be defined as Terraform code, while namespace-scoped Kubernetes identities remain least-privileged?

## Tracks
### A. OpenStack network baseline
- `terraform/modules/openstack-network/`: network, subnet, external network reference, router, interface, security group and a TCP/22 management rule restricted by `var.management_cidr`.
- `security-baseline/openstack-security-group-baseline.md`: intended access restrictions and validation criteria.

### B. Kubernetes identity baseline
- `kubernetes/security/rbac-baseline/`: a synthetic namespace, two dedicated ServiceAccounts, Roles and RoleBindings.
- `security-baseline/kubernetes-rbac-baseline.md`: denied/allowed access policy expectations.

The two tracks are deliberately independent. They are grouped here for provenance, **not** treated as a deployed integrated platform.

## Validation plan
1. Run `terraform fmt -check` and `terraform validate` with the proper OpenStack provider configuration on a disposable lab host. Review the plan before any apply.
2. Configure `management_cidr` to a trusted admin source, not `0.0.0.0/0`.
3. For Kubernetes, use `kubectl apply --dry-run=client` on the example manifests, then `kubectl auth can-i` in an isolated namespace to record approved versus denied actions.
4. Capture a redacted plan, access-denial results, changed-policy behavior and rollback evidence. Do not mark as validated from static files alone.

## Excluded material
The previous repo also contained an IDP portal, agent sandbox, Zero Trust governance records, 1000+ other files and historical evidence. Those items were **not** migrated as a working project or claimed as tested. Their reusable concerns should become future independent labs only after review. Preserve a Git mirror of the source before considering deletion.

## Provenance
Selected from `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. Reference material was edited minimally for neutral naming; any previous system-level validations do not transfer to this lab automatically.

## Combination rule
After the OpenStack networking and Kubernetes RBAC tracks pass independent checks, combine them with Labs 15 and 16 for a higher-level project, keeping evidence and integration status separate.


## Additional Kubernetes source examples
`reference/kubernetes/` preserves 16 further Ingress, workload, namespace, admission/manifest policy and readiness examples. These are source references, **not validated workload deployment**.
