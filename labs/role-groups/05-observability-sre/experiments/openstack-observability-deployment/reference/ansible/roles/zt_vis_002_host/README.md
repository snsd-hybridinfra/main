# ZT-VIS-002 host bootstrap role

This package-owned role prepares only the approved private Ubuntu monitoring
host before the five-component `zt_vis_002` role runs. It requires explicit
bootstrap and Cinder-checkpoint gates, an exact Terraform-state-sized empty
device, a private bind address, external mTLS files, and a controller-side offline DEB
bundle. The fixed Ubuntu package set is Podman, podman-compose, and Nginx.

The role copies a separately prepared, hashed Ubuntu package bundle and invokes
APT with `--no-download` while preventing transient Nginx startup. The target
does not receive external package-repository access. It formats only the reviewed empty device,
persists an `ext4,nodev,nosuid` mount at `/opt/snsd-zt-vis-002`, removes the
default Nginx listener, and starts Nginx only after the private mTLS proxy
configuration passes `nginx -t`. It never creates an OpenStack resource,
public endpoint, identity, certificate, key, or repository secret.

Trust material, package archives, inventory, device selection, target address,
and approvals remain external to Git. A failed bootstrap must stop before the visibility
role; infrastructure rollback continues to use the protected Terraform state
and Cinder snapshot, while service rollback preserves the mounted data.
