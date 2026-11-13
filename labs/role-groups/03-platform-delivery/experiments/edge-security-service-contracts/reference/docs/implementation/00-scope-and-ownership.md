# Scope and ownership

## Candidate scope

The public portal exposes eight approved composite blueprints and bounded
inputs. Five OpenStack execution profiles—three private Nova VM sizes and two
private single-node k3s PaaS sizes—are available only to service identities.
`VM_APPLICATION_STACK` persists an immutable resolved manifest through approval
and runner verification; other blueprints fail closed when a component adapter
is absent. Network, image, keypair, flavor, security groups, module digest,
tags, and lifecycle policy remain server-owned.

The candidate includes request, approval, Grant, expiry/revocation, Terraform
execution, static portals, database/recovery assets, and provider-neutral
Kubernetes deployment manifests. It does not include a public endpoint, a new
identity provider, an OpenStack control plane, a floating IP, or authoritative
monitoring onboarding.

## Ownership

| Owner | Responsibility |
|---|---|
| Portal service | Request schema, catalog projection, approval workflow, callbacks, expiry and revocation |
| Zero Trust identity/access owner | Authenticator, PEP route, audience/scope, administrator separation, Grant validation |
| OpenStack operator | Project, quotas, private network, security groups, Glance images, keypair, flavors, `clouds.yaml`, recovery path |
| Terraform operator | Reviewed module digest, protected state, runner identity, apply/destroy authorization and rollback |
| k3s platform owner | Approved base image, offline artifacts and digests, Ansible authority, namespace policy, restricted kubeconfig delivery and lifecycle |
| Visibility owner | Audit transport, metric/log onboarding, retention, alerting and sanitized evidence review |

## Handoffs

No infrastructure identifier or credential is committed. The operator injects
approved runtime values outside Git only after a separate deployment approval.
The k3s execution profile remains blocked until both OpenStack deployment and k3s
configuration authorizations are present. The playbook must prove API readiness,
baseline objects, policy enforcement, service enablement, and rollback without
returning a token or kubeconfig.

This candidate reuses existing package authorities; it does not introduce a new
package ID or change any package acceptance, maturity, or Phase 1 status.
