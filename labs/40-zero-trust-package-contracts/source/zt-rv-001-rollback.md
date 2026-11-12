# ZT-RV-001 Rollback

Rollback removes or reverts only the campaign definition, acceptance policy,
schemas, campaign tools, wrapper, inert tests, and generated ignored runtime
proposals after review. It must preserve the original verification history,
all accepted execution evidence, ZT-CV-001 and ZT-AUTO-001 tooling, existing
validators, package assessments, OpenStack, EVE-NG, router configuration, and
operator access.

A rejected candidate remains in ignored runtime storage until reviewed; it is
not deleted to hide a failure. A stale lock is reported and reviewed rather
than silently removed. No system, service, network, identity, schedule,
history, status, maturity, commit, or push action is an automatic rollback.
