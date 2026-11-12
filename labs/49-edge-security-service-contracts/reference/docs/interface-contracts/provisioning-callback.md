# Provisioning callback contract

The approval API owns the provisioning-job queue and lifecycle projection. The
Terraform runner owns only execution of a catalog-pinned OpenStack module.

## Lifecycle

`APPROVED -> PROVISIONING -> RUNNING` is accepted only when the callback has the
expected request, product, module version, artifact digest, private endpoint,
resource identifier, and successful post-apply validation. Any mismatch becomes
`PROVISION_FAILED`; it never creates a Grant.

Expiry or revocation first blocks the Grant and then follows
`DESTROYING -> TERMINATED`. Failed destroy remains explicit and requires operator
review. A destroy callback may not claim success without the expected state key
and validated runner identity.

## Runtime boundary

The repository defaults to `RUNNER_MODE=mock` and
`TF_OPENSTACK_DEPLOYMENT_AUTHORIZED=false`. Real execution additionally requires
an external `clouds.yaml`, an approved cloud/region/network/security-group/image/
keypair/flavor set, and protected Terraform state. No credential is accepted in
an API request or Terraform variable.

k3s catalog entries use an approved base Glance image and private Nova port.
After Terraform validation, the separately authorized and digest-pinned Ansible
playbook installs offline artifacts and verifies the API, core components, and
namespace controls. A Nova `ACTIVE` state alone is not PaaS validation. Ansible
failure triggers automatic Terraform destroy before the failed callback.
