# ADR 0017: Fix the Phase 2 visibility deployment-readiness boundary

- Status: Accepted for local preparation
- Date: 2026-08-21
- Package: ZT-VIS-002
- Action: P2-VIS-001
- Scope: supply-chain, access-role, retention, and restore design only

## Context

The dedicated Cinder LVM prerequisite is runtime validated, but the central
visibility deployment remains prohibited. The remaining design work must fix
immutable component inputs, a non-public access model, administrator and
recovery separation, and a bounded retention and restore method before a live
Terraform plan or Ansible deployment can be reviewed.

## Decision

The five visibility images are fixed to the reviewed Linux AMD64 manifests in
`docs/zero-trust/phase-2-visibility-readiness-contract.yaml`. The versions
match the existing repository visibility baseline for Grafana, Loki, and Alloy
and add fixed Prometheus and Blackbox Exporter versions. Tag-only references,
mutable fallbacks, and unreviewed substitutions are denied. The registry
mapping must be rechecked immediately before deployment. This decision does
not claim image signature verification or vulnerability assessment.

The exposure boundary is a private TLS reverse proxy with mutual TLS client
authentication, followed by Grafana authentication. Grafana anonymous access,
public endpoints, floating IPs, and direct non-loopback service listeners are
denied. The roles are separated as follows:

- `VISIBILITY_VIEWER` has read-only dashboard access.
- `VISIBILITY_ADMINISTRATOR` administers the visibility application through a
  separately held external secret.
- `RECOVERY_OPERATOR` uses key-only host access for service recovery and Cinder
  volume reattachment and receives no dashboard administrator role by default.

OIDC is intentionally deferred to P2-OIDC-001. Server certificates, the client
CA, client credentials, the Grafana administrator secret, OpenStack
credentials, inventory, and runtime state remain outside Git.

The initial retention selection is 336 hours. Loki and Prometheus data reside
on the dedicated Cinder volume. Recovery is based on reattaching the preserved
volume to a rebuilt monitoring VM. A Cinder snapshot is the reviewed rollback
checkpoint for the bounded deployment test, but snapshot and reattachment
success must be proven at runtime. No independent backup backend, RPO, RTO, or
disaster-recovery claim is made.

## Consequences

- The component-digest gate is locally closed.
- The proxy/role and retention/restore *design* gates are locally closed but
  remain runtime pending.
- Deployment remains NO-GO until an external OpenStack input bundle and proxy
  trust material are reviewed and separate deployment and live-validator
  authorization is recorded.
- No Terraform plan/apply, Ansible package playbook, image pull, central
  ingestion, package promotion, maturity assessment, or compliance assessment
  is authorized by this ADR.

## Follow-up on 2026-08-21

After explicit authorization for the sensitive administrator-profile transfer,
the external cloud profile and exact selected Terraform values were installed
on the dedicated control VM outside Git with mode `0600`. Source/target and
rendered-selection hashes matched. The local mTLS chain, server name, private
key permissions, and external Grafana administrator secret were also verified.
No control-node cloud authentication, Terraform plan/apply, proxy deployment,
or live validator was executed. Separate live-deployment and live-validator
authorization remains mandatory.

## Terraform preflight follow-up on 2026-08-21

After the next task was explicitly approved with its no-apply boundary, the
dedicated control VM installed Terraform 1.15.8 from the official HashiCorp
release after PGP fingerprint, signature, and archive SHA-256 verification.
The OpenStack provider remained fixed at 3.4.0; the dependency lock gained the
missing Linux AMD64 package hash while preserving the Windows hash and registry
checksums. Backend initialization, refresh, and state locking were disabled.

Provider authentication, `terraform init`, `terraform validate`, the saved
no-apply plan, and the JSON policy review passed. The plan contains zero prior
resources, exactly four approved create actions, and zero destructive actions.
The raw plan, JSON, logs, credentials, and exact inputs remain on the protected
control VM outside Git with mode `0600`; only the plan fingerprint and
sanitized structural result are authoritative here. No apply, Ansible
playbook, image pull, target mutation, proxy runtime verification, package
promotion, maturity assessment, or compliance assessment was performed.
Separate deployment and live-validator authorization remains mandatory.
