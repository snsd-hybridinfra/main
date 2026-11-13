# Lab 36: Day-2 Operations & Failure Recovery Runbooks

**State:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. All **40 files** under the original `docs/runbooks/` path were copied as historical operational design references. No runbook execution or cloud provisioning was performed.

## Core question
How do infrastructure operators coordinate preflight, deployment approval, drift response, backup, restore, incident response, upgrade and decommissioning with deterministic gates and auditable evidence?

## Structure
- `reference/00-*.md` through `28-*.md`: platform lifecycle and Day-2 processes
- `reference/phase-1/`: foundation/read-only validation and evidence procedures
- `reference/RUNBOOK_INDEX.md`, `reference/RUNBOOK_TEMPLATE.md`: catalog and template

## Adaptation rules
1. **Do not copy commands into a live environment.** Original docs contain product-specific paths, service names, endpoints or assumptions.
2. Extract a runnable, isolated mini-runbook per concern (e.g. link failure, alarm triage, backup/restore), with prerequisites and no-production-data safeguards.
3. Require operator approval and a rollback boundary for changes; run only in an isolated lab.
4. Log normal, denied, failed, recovered results with sanitized timestamps and evidence.
5. Link completed runbooks to Labs 15–33, but do not claim deployment success from documentation alone.

## Attribution
Original `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `docs/runbooks/`.
