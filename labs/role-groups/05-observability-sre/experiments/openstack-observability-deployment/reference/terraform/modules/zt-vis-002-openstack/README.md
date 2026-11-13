# ZT-VIS-002 private OpenStack monitoring VM module

This local-preparation module creates exactly one existing-network Neutron port,
one Nova VM, one Cinder data volume, and one volume attachment. It does not
create networks, subnets, routers, security groups, identities, credentials, or
floating IPs.

All network, security-group, image, flavor, keypair, capacity, storage, and
approval inputs must be reviewed before a plan is generated. OpenStack
authentication comes from an external `clouds.yaml`; state and plan files stay
outside Git. Outputs contain resource identifiers and a private address only.

This module has not been initialized, planned, or applied in the current
package. Its presence is local implementation preparation, not deployment or
runtime evidence.
