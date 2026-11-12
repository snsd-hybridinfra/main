# Argo CD bootstrap boundary

`idp-container-release-application.yaml` is a prepared bootstrap declaration.
It is not evidence that Argo CD or the application is installed. A platform
operator must review and install this Application once on the approved k3s
control plane. From then on it reads only `main` and reconciles the digest-only
desired state under `kubernetes/releases/`.

The CI workflow never receives kubeconfig and cannot apply this declaration or
workloads directly.
