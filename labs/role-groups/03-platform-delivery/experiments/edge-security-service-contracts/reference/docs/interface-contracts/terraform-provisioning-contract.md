# OpenStack Terraform provisioning contract

The Terraform runner uses a named entry in an external `clouds.yaml`. An
OpenStack application credential scoped to the dedicated lab project is the
preferred runtime identity. No credential field is accepted from a user or
written to approved tfvars.

Every job is bound to request ID, owner, product ID/version, module version,
module digest, approver, expiry, purpose, and mandatory metadata. Modules are
content-hashed again immediately before execution.

The provider boundary is Keystone, Glance, Nova, and Neutron only. Modules may
create one port and one instance. They reuse existing network, security groups,
image, key pair, and flavor. They may not create public addresses or control-
plane resources.

The checked-in candidate does not authorize execution. A deployment review must
supply the explicit runtime switch, credential file, protected state root,
approved provider inputs, private egress, rollback plan, and k3s configuration
authorization. k3s additionally needs an approved base image, strict SSH host
authority, external SSH identity, digest-pinned offline binary/image artifacts,
and the reviewed Ansible digest. Debug logs must remain disabled unless
separately approved and sanitized because provider and configuration logs can
contain sensitive material.
