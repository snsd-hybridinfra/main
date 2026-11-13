# Lab 34: PostgreSQL Schema, RBAC and Alembic Migrations

**State:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. All 26 text files from the old IDP `database/` subtree are retained as reference material; no schema or Alembic command has been run in this destination.

## Experiment question
Can isolated request/control/identity PostgreSQL schemas be provisioned, upgraded, and reverted while maintaining least-privilege roles and preventing unauthorized cross-schema access?

## Source structure
- `source/migrations/`: Alembic configurations and version scripts for request/control DBs
- `source/schema/`: original SQL schemas
- `source/roles/`: DB role and grant examples
- `source/verification/`: access validation scripts

## Safety and reproducibility
- Treat original DB roles, migration URLs and schema owners as **examples** until audited.
- Do **not** run migration scripts or SQL grants against existing databases. Only use a fresh synthetic PostgreSQL container with a disposable database and a non-admin test principal.
- Verify upgrade → expected schema → idempotency or repeat failure → privilege-denial cases → downgrade/rollback independently.
- Align DB schema versions with [Lab 27 Request API](../self-service-request-api/README.md) and [Lab 28 Approval/Grant](../approval-grant-lifecycle/README.md) **only after** each lab's own test harness is ready.
- Historical migrations can include destructive schema changes. Inspect all `DROP`, `ALTER` and backfill statements before execution.

**Source:** [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops), commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef` at `applications/internal-iaas-portal/database/`.
