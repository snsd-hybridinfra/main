# OpenStack Terraform runner

The runner consumes approval-owned fixed jobs and defaults to `mock`. Real mode
fails closed unless `TF_OPENSTACK_DEPLOYMENT_AUTHORIZED=true` and all reviewed
OpenStack inputs are present.

Required real-mode inputs are `OS_CLIENT_CONFIG_FILE`, `OS_CLOUD`,
`OS_REGION_NAME`, `TF_OPENSTACK_NETWORK_ID`,
`TF_OPENSTACK_SECURITY_GROUP_IDS`, `TF_OPENSTACK_APPROVED_IMAGE_NAME`,
`TF_OPENSTACK_APPROVED_K3S_IMAGE_NAME`, `TF_OPENSTACK_KEYPAIR_NAME`, and the
three approved flavor names. The credentials file and Terraform state are
runtime-only and must be protected outside Git.

Jobs accept only `APPLY` or `DESTROY`, bounded job/request identifiers and the
exact state key `requests/<request_id>/terraform.tfstate`. Approved input
request/product/version values and ownership/expiry tags must agree with the
job. This prevents a job from selecting another request's state.

`TERRAFORM_WORK_ROOT` and `TERRAFORM_STATE_ROOT` must be absolute, disjoint
external paths. Credentials and SSH trust/key references must be absolute and
outside Git and the disposable work root. Resolved workspace/state paths must
not redirect through a symlink. All checks happen before file creation or
Terraform commands. A pre-existing job workspace requires reviewed recovery;
the runner never replaces it automatically. Cleanup removes only the workspace
exclusively created by the current invocation, leaving external state and
credential material intact on rejection or failure.

The customized supply-chain wrapper also requires
`TF_TERRAFORM_BINARY_SHA256`, `TF_SUPPLY_CHAIN_LOCK`,
`TF_TERRAFORM_CATALOG`, `TF_PROVIDER_MIRROR_ROOT`,
`TF_OPENSTACK_PROVIDER_PACKAGE`, and
`TF_OPENSTACK_PROVIDER_PACKAGE_SHA256`. The provider mirror, package and CLI
digest are external reviewed runtime inputs; the runner generates a
filesystem-mirror-only CLI configuration and does not contact the provider
registry.

k3s apply additionally requires `TF_K3S_CONFIGURATION_AUTHORIZED=true`, an
approved SSH remote user, private-key path, strict known-hosts authority,
runner-local k3s binary and matching air-gap image archive, and SHA-256 for both
artifacts. `ansible-core` 2.21.2 is pinned in the runner image. None of these
runtime files belongs in Git.

Before apply, the runner verifies the catalog and module authorities, exact
module file set, Terraform CLI version/digest, OpenStack provider
source/version/package digest, and the saved plan JSON. Only exact `create` or
`no-op` actions for one port and one instance may apply. Destroy and automatic
rollback use an inspected saved destroy plan with only `delete` or `no-op`;
replacement, update, import, provider substitution and uninspected destroy are
denied.
After every destroy, including automatic k3s rollback, the runner reads the
Terraform state again and requires no resources in the root or any nested
module. Invalid, unsupported or unreadable state fails closed as
`DESTROY_FAILED` or `ROLLBACK_FAILED`; a successful command alone cannot produce
`TERMINATED` or a rollback-success claim. This is a local state check, not
independent OpenStack resource-absence evidence.
After apply, it rejects any state other than one Neutron port and one Nova VM,
checks private addressing, port security, exact security groups, image, flavor,
key pair, metadata, and the absence of a Floating IP. For k3s, the runner then
executes the digest-pinned Ansible playbook, validates API readiness and the
declared platform components, and returns `READY`. Once apply has started, an
apply-command failure, malformed output, state-policy failure, or k3s
configuration failure triggers an inspected destroy plan. The runner reports
`ROLLED_BACK` only after the post-destroy Terraform state is proven empty; an
unreadable or non-empty state reports `ROLLBACK_FAILED` and never authorizes a
Grant. Recovery reports contain only bounded status and failure-code fields,
and the approval API records those fields in the provisioning-job audit stream.
