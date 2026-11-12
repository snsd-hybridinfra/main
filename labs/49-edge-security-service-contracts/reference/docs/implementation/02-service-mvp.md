# OpenStack service candidate

## User flow

1. The user selects an approved composite blueprint and bounded environment, size, duration and purpose inputs.
2. The request API resolves and hashes an immutable manifest or rejects an unimplemented component.
3. An authorized approver receives the catalog-pinned manifest and internal execution profile.
4. The runner independently verifies the manifest, execution profile, module digest, inputs and ownership tags.
5. A successful private-resource validation creates the bounded Grant.
6. Expiry or revocation blocks access before Terraform destroy.

## PaaS profile

The k3s execution profiles are single-node development PaaS candidates. Terraform creates
only an approved base-image Nova VM and private Neutron port. Ansible verifies
and copies an offline k3s binary and matching air-gap image archive, enables
secret encryption, disables bundled ingress and service load balancing, and
creates the private platform and `dev` namespace policy.

No join token or kubeconfig is a Terraform or Ansible result. Mock mode
exercises the API contract only. Real automation requires separate OpenStack and
k3s configuration authorizations; Ansible failure automatically destroys the
newly created instance and port.

## Current result

The application and Terraform policy are locally testable candidates. The
`VM_APPLICATION_STACK` blueprint path is locally implemented through independent
runner manifest verification; other blueprints remain adapter-blocked. Cluster
manifests retain deliberately invalid image and endpoint placeholders, so static
release readiness is expected to remain `NO-GO` until reviewed deployment inputs
and runtime evidence exist.
