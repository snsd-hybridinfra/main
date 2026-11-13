# OpenStack Terraform product modules

`catalog.json` is the fixed product authority for three private Nova VM products
and two private single-node k3s PaaS products. Each module creates exactly one
Neutron port and one Nova instance.

The runner, not the requester, supplies the named `clouds.yaml` entry, region,
existing network ID, existing security-group IDs, approved image name, existing
key pair, and approved flavor. Application credentials remain in the external
`clouds.yaml`; they are never Terraform variables or committed files.

The base uses a local backend path under the runner's protected state root
because the current lab has no accepted Swift or other remote-state service.
Real deployment requires encrypted, access-controlled, backed-up storage and
separate authorization. State files, `.terraform/`, plans, logs, and tfvars are
ignored and must not be committed.

Denied by design: Floating IP, network/subnet/router/security-group/identity
creation, arbitrary HCL, arbitrary module paths, unapproved image/flavor, and
Grant before Ansible k3s configuration and validation. Terraform owns only the
Nova/Neutron resource lifecycle; the digest-pinned Ansible authority owns the
k3s operating-system and PaaS baseline.

`supply-chain-lock.json` independently binds the catalog, the five module
digests, upstream Terraform 1.16.1, OpenStack provider `~> 3.4.0`, exact resource
counts and saved-plan action policy. Customization is implemented in the
repository-owned runner policy layer; Terraform core is not forked.
