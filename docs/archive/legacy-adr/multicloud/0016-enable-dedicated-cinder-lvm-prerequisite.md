# ADR 0016: Enable a dedicated Cinder LVM prerequisite

- Status: Accepted
- Date: 2026-08-21
- Scope: P2-VIS-001 OpenStack storage prerequisite only

## Context

The P2-VIS-001 live-gate discovery found sufficient compute capacity and the
required private OpenStack resource candidates, but no block-storage service or
volume-v3 endpoint. The existing secondary AIO disk is authoritative Nova
instance storage and cannot be reused. The root volume group has free space,
but sharing it with a new storage backend would couple control-plane and volume
failure domains.

Kolla-Ansible 2026.1 documents a dedicated `cinder-volumes` volume group and
`enable_cinder_backend_lvm: "yes"` for the LVM backend. Its 2026.1 inventory
groups already map the LVM volume, backup, iscsid, and tgtd services to the
single-node laboratory storage host.

## Decision

Attach one new 100 GiB thin VMware disk at the reviewed SCSI 0:2 slot of the
OpenStack AIO VM. Use only the resulting new block device for the
`cinder-volumes` physical and volume group. Preserve the root disk and the
existing Nova instance-storage disk without repartitioning, signatures, or
volume-group changes.

Enable Kolla Cinder and its LVM backend, retain a restricted pre-change backup
of Kolla globals and inventory, install the official Kolla collection
dependencies required by the installed 2026.1 development build, and deploy
only the Cinder and iSCSI tags after the aggregate HAProxy and ProxySQL
configuration is regenerated. Explicitly disable `cinder-backup`: the default
driver is Ceph, while this laboratory has no approved Ceph, NFS, or S3 backup
backend and retention/restore approval remains open. The laboratory continues to use the matching
Kolla 2026.1 test-image channel; this is not a production image decision.

The repository stores only the bounded disk-attachment helper, this decision,
and sanitized evidence. VMX files, VMDKs, host configuration, credentials,
resource identifiers, addresses, raw logs, and backups remain outside Git.

## Validation

- Kolla prechecks passed after the official collection dependencies were
  installed.
- HAProxy and ProxySQL accepted the Cinder service and database routes.
- Cinder API, scheduler, LVM volume, iscsid, and tgtd started; all
  health-enabled Cinder containers became healthy.
- The block-storage service has internal and public service-catalog endpoints,
  and scheduler and volume services are enabled and up.
- A reboot check exposed the unsupported default Ceph backup driver. The
  configuration was corrected to disable backup, its stale container was
  removed, and the service record is intentionally `disabled/down` pending a
  separately approved backup backend.
- A temporary 1 GiB volume became available and created exactly one backend
  logical volume.
- Unauthenticated and invalid-token API requests both returned HTTP 401.
- After a full AIO reboot, the dedicated device, volume group, services,
  temporary volume, and backend logical volume remained available.
- The temporary volume was deleted; both OpenStack and backend temporary-volume
  counts returned to zero.
- The two originally active validation VMs were restored to active state, and
  the originally stopped general Ubuntu VM remained stopped.

## Consequences

- The earlier missing-Cinder prerequisite is closed and runtime validated for
  this non-production AIO only.
- P2-VIS-001 central visibility deployment remains NO-GO. The external
  Terraform cloud profile, immutable component digests, authenticated proxy,
  administrator and recovery roles, retention and restore decisions, and
  separate stack deployment/validation gates remain open.
- ZT-VIS-002 remains `LOCAL_PREPARATION_ONLY / LOCAL_VALIDATED /
  NOT_VALIDATED / PENDING`. Cinder activation is not central monitoring
  deployment, package runtime acceptance, backup/restore validation, maturity,
  compliance, certification, or production readiness.
- The tested rollback boundary removed only the temporary validation volume.
  Full Cinder removal is intentionally unexecuted while the prerequisite is
  required. It requires a separate approval, dependency review, the retained
  Kolla backup, service disablement, volume-group cleanup, AIO shutdown, and
  exact SCSI 0:2 disk detachment.

## References

- https://docs.openstack.org/kolla-ansible/2026.1/reference/storage/cinder-guide.html
- https://docs.openstack.org/releasenotes/kolla-ansible/2026.1.html
