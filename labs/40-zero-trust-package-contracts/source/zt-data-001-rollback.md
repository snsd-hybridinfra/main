# ZT-DATA-001 Rollback

Rollback is repository-only and operator-reviewed. It is not executed during
normal validation.

1. Confirm the target diff contains only ZT-DATA-001-owned inventories,
   policies, schemas, validators, tests, telemetry additions, package records,
   evidence summaries, and tracking updates.
2. Preserve all original source data, existing backups, OpenStack/EVE-NG
   services, application and telemetry workloads, identity and endpoint
   controls, restricted validators, and operator access.
3. Revert package-owned inventory, label, access, DLP, scanner, wrapper,
   telemetry, fixture-catalog, schema, documentation, and sanitized evidence
   files through a reviewed version-control change.
4. Do not automatically delete `.runtime/zero-trust/data/`. After evidence
   review, the operator may remove only the exact generated synthetic run
   directories. Never use a broad or unresolved path.
5. Re-run Zero Trust, synchronization, report, scenario-lock, secret, and
   runtime-ignore validation. Restore prior tracking language if the package
   authority is removed.

Rollback never decrypts, deletes, relocates, overwrites, exports, backs up, or
restores a live data source. It never rotates credentials or keys and never
changes a blocking DLP or platform policy.
