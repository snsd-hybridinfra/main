# ZT-VIS-002 configuration role

This role configures the fixed Grafana, Loki, Alloy, Prometheus, and Blackbox
Exporter stack only after explicit deployment, authenticated-proxy, storage,
secret, probe-target, digest, offline OCI archive, and Podman gates pass. It
installs no package, performs no registry download, creates no identity, and
opens no public listener.

Every image variable must be an immutable `repository@sha256:<digest>` value.
The role defaults contain the locally reviewed Linux AMD64 manifest set and an
exact-value assertion rejects substitutions. Registry resolution must still be
rechecked immediately before an authorized deployment; signature and
vulnerability assessment are not implied by digest pinning.
The five OCI archives are copied from protected controller paths, loaded into
local Podman storage, checked against the reviewed digest references, and then
removed from target staging. The Grafana administrator secret is copied from an external controller file
with `no_log`; credentials and raw runtime output are not emitted. All host
ports bind to loopback. The authenticated reverse proxy and operator recovery
path are external prerequisites, not created by this role.

The role and both package playbooks pass native Ansible 2.16.3 syntax checks
on the dedicated Ubuntu 24.04 VMware control node. The deploy playbook uses its
repository-relative role path so it does not depend on a host-global Ansible
configuration. The control node is not package runtime authority and does not
contain an approved live inventory or OpenStack credential.

The role was exercised by the separately authorized one-time live validator.
It enables `podman-restart.service`, uses the `always` restart policy for all
five containers, and restores the package-owned Compose project after a target
restart. The accepted campaign passed restart persistence, package-only stack
removal, preserved-data recovery, configuration-integrity, and mTLS checks.
Runtime inputs remain outside Git. A full Cinder snapshot rebuild and
reattachment restore, package status promotion, and production claims require
separate approval.
