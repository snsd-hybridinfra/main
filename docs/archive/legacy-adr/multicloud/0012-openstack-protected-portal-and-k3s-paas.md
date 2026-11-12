# ADR 0012: OpenStack protected portal and k3s PaaS candidate

- Status: Accepted for local candidate architecture
- Date: 2026-08-12
- Decision authority: repository architecture and scope governance

Catalog taxonomy note: ADR 0019 reclassifies these five entries as internal
provider-bound execution profiles beneath the approved composite blueprint
catalog. This ADR continues to govern their provider and rollback boundary.

## Context

The supplied `F:/2차프로젝트.zip` described an AWS-oriented internal cloud
portal. The project direction requires the portal to become a Zero Trust
protected system on the existing OpenStack axis, with developer PaaS supplied
by k3s rather than a public-cloud managed service.

The source archive SHA-256 is
`3cda17c993e17465676f607410a03f16d7ff0648a62ed403abea133950b4edb3e8`.
Credentials, virtual environments, caches, bytecode, raw historical evidence,
and obsolete provider plans were excluded from adoption.

## Decision

Adopt the sanitized application under `applications/internal-iaas-portal/` and
use five fixed products: three private Nova VM profiles and two private,
single-node k3s profiles. Each Terraform module may create exactly one Neutron
port and one Nova instance. It consumes an existing operator-approved network,
security groups, Glance image, keypair, and flavor; it may not create a network,
router, security group, identity, or Floating IP.

k3s starts from an approved base Glance image. After Terraform validates the
private instance and port, a separately authorized, digest-pinned Ansible
playbook verifies and copies an approved k3s binary and matching air-gap image
archive. It configures the kernel, systemd service, encrypted secrets, core
components, and namespace policy without a network installer. Terraform and
Ansible do not output a token or kubeconfig. Ansible failure automatically
invokes Terraform destroy; rollback failure is an explicit blocking state.

The portal is mapped as a candidate protected system to existing package
authorities. It is not added to the authoritative ZT-APP-001 application counts
and does not alter any package, capability, maturity, or Phase 1 status.

## Consequences

- Local mock and policy validation can proceed without cloud credentials.
- A live VM deployment requires separate authorization and reviewed runtime
  inputs outside Git.
- k3s additionally requires a strict SSH host authority, external automation
  identity, offline artifact digests, API/core-component/baseline-policy checks,
  and successful configuration before a Grant can be issued.
- Placeholder container digests, identity endpoints, private DNS, network
  ranges, secrets delivery, monitoring, and recovery keep deployment `NO-GO`.
- The application can be promoted only through the existing package and
  evidence authorities; this ADR is not runtime evidence.
