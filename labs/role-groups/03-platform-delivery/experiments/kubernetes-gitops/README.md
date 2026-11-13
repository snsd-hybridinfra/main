# Lab 31: Kubernetes Manifest, Policy & GitOps Source

**Status:** `MIGRATED / NOT_REVALIDATED`. **All 63 files** from the prior IDP `applications/internal-iaas-portal/kubernetes/` source directory are preserved as reference material, without automatic deployment or GitOps reconciliation.

## What can be studied
- Deployment and Services for request, approval, grant, runner, edge and portal components
- Namespaces, ServiceAccounts, NetworkPolicies, PodDisruptionBudgets, CronJobs and configuration
- Security separation, Istio mTLS/AuthZ and GitOps Application patterns

## Boundary and prerequisites
These source manifests reference the *old* image registry, application services, secrets, cluster add-ons and environments. They are **not safe to apply unchanged** and may include resource names, image references and domain dependencies from the old test architecture.

## Revalidation plan
1. Parse YAML and verify Kustomize build outputs in a disposable workspace.
2. Replace image registry and public DNS values with local non-production placeholders.
3. Audit image digest pins, all RBAC permissions and explicit default-deny NetworkPolicies.
4. Verify denied traffic, mTLS enforcement, PDB disruptions, supply-chain integrity and rollback in an isolated kind/k3s cluster.
5. Do not enable automatic GitOps sync until manual validation and unique namespace/resource boundaries are complete.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops`, commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. Contents copied into `source/`, outside any root deployment workflow.
