# ADR 0023: Container Image Supply Chain and k3s Delivery

- Status: Accepted for local implementation
- Date: 2026-08-28
- Decision authority: operator direction to extend the managed supply chain through CI/CD image installation
- Architecture authority: `ZT-ARC-001`

## Context

The central IDP has seven buildable service images and Kubernetes workload
manifests, but the manifests intentionally contain unresolved zero digests. A
tag-only build or a CI job that directly replaces those values would not prove
which source, base image, scanner result, SBOM, signature or provenance was
approved. It would also mix artifact production with an unreviewed cluster
mutation.

The Terraform supply chain in ADR 0022 provisions the bounded OpenStack/k3s
service plane. The container supply chain is a separate authority that produces
and installs the application artifacts which run on that plane.

## Decision

Adopt the following fail-closed release path:

```text
reviewed source commit
  -> repository policy and unit tests
  -> approved digest-pinned base images
  -> isolated BuildKit build with SBOM and provenance
  -> vulnerability policy (zero HIGH and CRITICAL findings)
  -> OCI registry push by immutable digest
  -> keyless/workload-identity signature and attestation verification
  -> immutable resolved release manifest
  -> protected publish approval
  -> reviewed GitOps promotion pull request
  -> merge-approved digest-only desired state
  -> Argo CD reconciliation to k3s
  -> sanitized sync/health evidence or Git revert rollback
```

`applications/internal-iaas-portal/supply-chain/container-supply-chain-lock.json`
is the machine authority for the seven image identities, Dockerfiles, required
base-image inputs and Kubernetes consumers. Users cannot select a Dockerfile,
registry, image name, tag, scanner exception or target cluster through the
product request.

CI may validate pull requests and build disposable images. Publishing, signing
and promotion run only from a reviewed main commit on a hardened runner behind
a protected environment. CI has no kubeconfig and does not call `kubectl apply`;
it writes a sanitized immutable release and updates the GitOps pointer on a
dedicated branch. Installation begins only after that promotion pull request is
reviewed and merged. Argo CD reconciles `main` to the approved k3s destination.

The cluster receives only a generated digest overlay whose release attestation
has the exact locked image set, source commit, SBOM digest, provenance result,
signature verification and vulnerability decision. Mutable tags, zero digests,
partial releases, unapproved registries, direct user manifests and unsigned
images fail closed.

The GitOps overlay updates only the locked Deployment and recurring CronJob
workloads. Namespaces, service accounts, configuration, secrets, services,
network policies and database migrations are service-plane prerequisites owned
by their existing authorities. Fixed-name migration Jobs are intentionally
excluded from image rollout so an immutable Job-spec conflict cannot bypass the
database migration procedure.

## Consequences

- Terraform and container supply-chain status remain independent.
- Registry credentials, signing material, kubeconfig and raw scan reports stay
  outside Git. Sanitized immutable release authorities and digest-only overlays
  are reviewed in Git.
- The repository can validate the release machinery locally without claiming a
  registry push or k3s installation.
- A live publish or install requires external toolchain artifacts, workload
  identity, registry trust, a protected runner, Argo CD and a separately
  approved promotion merge.
- This decision adds no public-cloud, production, compliance or Zero Trust
  maturity claim.
