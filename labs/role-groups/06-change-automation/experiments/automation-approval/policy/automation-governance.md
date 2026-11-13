# Automation Governance

ZT-AUTO-001 is owned by the laboratory repository maintainer and security
review function. It governs a fixed-handler validation orchestrator on one
workstation; it does not delegate production change authority.

## Registration and review

Every action needs a unique ID, one reviewed handler ID, purpose, risk,
approval, fixed argument contract, working-directory boundary, timeout,
idempotency statement, evidence requirement, telemetry events, rollback type,
tests, and limitations. Every workflow needs an acyclic dependency graph,
explicit conditions, failure behavior, result criteria, output boundary, and
capability mapping. Catalog and code changes require review together; a YAML
entry cannot make an implementation executable.

Risk is classified R0 through R8. Only R0-R3 can execute in this package. R4
through R7 remain non-executable future controls and R8 is prohibited. R2
requires operator review; R3 requires operator approval or a previously
accepted fixed package policy. An approval binds the exact immutable plan hash,
scope, expiry, and risk. A committed approval string never proves that a person
approved an execution.

## Execution, secrets, and audit

Execution authority must distinguish check, plan, local, live runtime, and
proposal-only work. Fixed child processes use argument arrays, `shell=False`,
positive parameter allowlists, a sanitized environment allowlist, explicit
timeouts, no password prompts, and no hidden privilege fallback. Locks contain
owner metadata and are retained or reported safely when stale.

Raw output, locks, plans, execution records, and proposals live under ignored
`.runtime/zero-trust/automation/`. Only reviewed sanitized aggregates may enter
`docs/evidence/`. Tokens, passwords, keys, credential values, approval
credentials, full usernames, full address inventories, full configurations,
and personal workstation activity are prohibited. Exit codes and mandatory
failures must never be ignored.

## Change control and exceptions

Any new executable handler, live destination, R4-R7 action, external
notification, identity integration, service restart, network or access change,
credential operation, or recovery action requires separate architecture,
security, rollback, testing, and explicit change approval. An exception must
name an owner, scope, expiry, risk, compensating control, evidence, and removal
plan; it cannot be encoded as a permissive wildcard.

Rollback removes only package-owned catalogs, schemas, tools, tests, and
generated runtime artifacts. Existing validators, virtual infrastructure,
network configuration, identities, telemetry services, workloads, data,
system baselines, operator access, and evidence are preserved.

Deprecated actions are first made non-executable, removed from workflows, and
retained as a reviewed reference until evidence and rollback dependencies are
cleared. Catalogs, permissions, live integrations, stale locks, failed runs,
exceptions, and maturity proposals are reviewed at each package change and
before any repeatability or scheduled-runtime campaign. Incident findings are
review proposals until a human confirms them.

Prohibited patterns include arbitrary shell execution, unrestricted SSH,
caller-controlled targets or executables, wildcard sudo, embedded passwords,
automatic production remediation, hidden fallback behavior, ignored exit
codes, unbounded retries, unsanitized evidence, direct authoritative-document
mutation, and automatic blocking, isolation, restart, reconfiguration,
credential rotation, deletion, or recovery.
