# ZT-DEV-001 device and endpoint authority

This directory is the bounded device-inventory and endpoint-compliance
authority for `ZT-DEV-001`. The inventory uses stable aliases and excludes IP
addresses, MAC addresses, hardware serials, usernames, personal application
lists, credentials, and full software-package exports.

Only `ZTD-ASSET-MONITORING-VM-01` is a mandatory live pilot. Other virtual-lab
assets remain constrained to their existing restricted validators or declared
inventory state. The Windows operator device and all physical infrastructure
remain outside endpoint collection.

`endpoint-compliance-policy.yaml` is detection-only: automatic remediation,
patching, reboot, isolation, and endpoint-agent installation are disabled.
Runtime data belongs under `.runtime/zero-trust/endpoint/` and is never an
authoritative committed inventory.
