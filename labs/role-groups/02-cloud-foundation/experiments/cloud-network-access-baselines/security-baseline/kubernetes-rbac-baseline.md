# Kubernetes RBAC Baseline

This repository-side baseline defines non-production RBAC policy only. It does not connect to or configure a Kubernetes cluster.

## Least Privilege RBAC Principle

- Namespace-scoped `Role` and `RoleBinding` are preferred over `ClusterRole` and `ClusterRoleBinding`.
- ServiceAccount separation by workload is required for `<application-workload>`.
- The `default` ServiceAccount must not be used for application workloads.
- No `cluster-admin` binding is permitted for application workloads.
- No wildcard apiGroups, resources, or verbs are permitted unless separately justified outside this baseline.
- Monitoring uses `<monitoring-service-account>` with read-only `get`, `list`, and `watch` verbs where possible.
- Write privileges are limited to specific approved workload automation use cases.
- Secrets access is denied by default and is not granted to application workloads.
- Namespaced identities use `<namespace>`, `<service-account>`, `<role-name>`, and `<rolebinding-name>` placeholders in policy documentation.

## Evidence Collection Model

- Run the local validator without `kubectl`, kubeconfig, or API server access.
- Store generated evidence below `<evidence-path>`.
- Record every validation result by stable check ID.
- Reject tokens, certificates, private keys, cluster endpoints, public addresses, Secret resources, and account-specific content.

