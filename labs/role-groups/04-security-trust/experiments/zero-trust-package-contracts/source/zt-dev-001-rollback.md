# ZT-DEV-001 rollback

Normal validation is read-only and needs no remote rollback. If repository
artifacts must be withdrawn, remove only the ZT-DEV-001 inventory, policy,
schemas, tools, tests, documentation, and sanitized evidence in a reviewed Git
change. Raw execution data under `.runtime/zero-trust/endpoint/` is ignored and
may be discarded through the normal local runtime-retention process.

No package, patch, endpoint agent, scheduled task, service, account, firewall
rule, router configuration, monitoring configuration, or credential was added
by this package. Rollback must preserve OpenStack, EVE-NG, router ACLs,
ZT-ID-001 restricted identities, Grafana/Loki/Alloy, operator access, and all
unrelated host state. If a later agent pilot is approved, its own snapshot,
health, uninstall, telemetry, and resource-impact rollback must be tested
before installation.
