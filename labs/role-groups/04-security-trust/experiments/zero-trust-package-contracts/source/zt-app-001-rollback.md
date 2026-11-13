# ZT-APP-001 rollback

ZT-APP-001 performs no deployment, restart, image pull, registry push,
signature operation, or runtime configuration change. Normal rollback is a
reviewed removal of only its inventories, policy, schemas, validators, scan
wrapper, tests, documentation, generated partial SBOM, and sanitized evidence.
Ignored data under `.runtime/zero-trust/application/` may be discarded through
the local runtime-retention process.

Rollback must preserve application source, current Alloy/Loki/Grafana
containers and volumes, OpenStack, EVE-NG, router configuration, identity
endpoints, endpoint tooling, telemetry configuration, operator access, and
unrelated images. Any future pilot configuration change requires its own
pre-change backup, tested restoration, explicit owner, and post-rollback
health check before execution.
