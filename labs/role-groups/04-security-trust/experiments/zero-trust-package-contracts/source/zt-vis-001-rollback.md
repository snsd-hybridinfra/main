# ZT-VIS-001 Rollback

Normal validation does not execute rollback. A reviewed repository change may
remove the local telemetry tools, schemas, event/rule catalogs, wrapper, tests,
and generated package evidence. Ignored files below
.runtime/zero-trust/telemetry/ may be removed locally after confirming they are
not required for review.

For the accepted persistent increment, run Compose down for only the
`snsd-zero-trust-visibility` project on the dedicated monitoring VM. Preserve
`/opt/snsd-monitoring/data`, the VM-local secret file, the VM, Docker runtime,
networking, and operator access until a separate deletion approval exists.
Temporary image-transfer infrastructure was already removed after deployment.

Preserve OpenStack, EVE-NG, router configuration, all existing validators,
operator access, unrelated Docker images or volumes, and retired numbered scenario framework.
