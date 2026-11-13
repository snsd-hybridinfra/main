# Terraform and Ansible runner deployment

This is the single control-service runner. `Recreate` plus database-backed job
claiming prevents concurrent ownership, and the pod exposes no listener.

The checked-in base is deliberately `RUNNER_MODE=mock` with both OpenStack and
k3s configuration authorizations false. It does not mount `clouds.yaml`, an SSH
identity, known-hosts authority, Terraform state, or k3s offline artifacts.

A reviewed live overlay must provide all runtime material from external secret
and artifact authorities, mount encrypted and backed-up state, keep the root
filesystem read-only, and set both authorization switches only for the approved
window. OpenStack application credentials are preferred over a long-lived user
password. k3s SSH must use strict host-key checking and a target-local automation
identity with only the required privilege.

That overlay must also mount the approved provider filesystem mirror and set the
Terraform CLI/provider package SHA-256 inputs documented by the runner. Direct
provider-registry egress, tag-only provider selection and an uninspected plan
remain denied.

The broad HTTPS egress placeholder exists because base Kubernetes NetworkPolicy
cannot express FQDN destinations. It must be replaced by Cilium FQDN policy or a
firewall proxy restricted to the identity and OpenStack API endpoints. The
private SSH path to the newly created Nova port must be separately approved.
