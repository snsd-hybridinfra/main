# Lab 20: PostgreSQL Backup + Restic Evidence Verification

**Status:** `MIGRATED / NOT_REVALIDATED`. This is source extraction for isolated testing, not a verified restore or backup deployment.

## Goal
Understand a controlled PostgreSQL logical backup path, Restic snapshot verification, integrity checks and credential capability denial. Complement Lab 05's synthetic recovery model and Lab 16's OpenStack operational baseline.

## Extracted scripts
- `scripts/backup-postgres.sh`: `pg_dump` in PostgreSQL custom format, snapshot manifest and SHA-256, then Restic backup
- `verification/verify-latest-snapshot.sh`: read snapshot into an isolated temporary directory, validate `SHA256SUMS` and `pg_restore --list`. This **does not perform database restore or application recovery**.
- `scripts/restic-check.sh`: list snapshots and check a subset of repository data
- `verification/verify-append-only.sh`: canary backup then negative delete authorization test. **WARNING: it invokes `restic forget`; use only a disposable Restic repository with a deliberately append-only credential.** Added mandatory `LAB_ALLOW_RESTIC_CANARY=YES` gate.
- `restic/*.env.example`: non-secret templates for a disposable lab only

## Validation gates before any use
1. Use a disposable local PostgreSQL instance and a separate disposable Restic repository. Ensure the account has no route to work or personal production databases.
2. Review PostgreSQL schema names (`request_service`, `control_service`, `keycloak`) and create matching synthetic schema fixtures or adapt them for a local test. The source scripts are **not generic one-command setup**.
3. Set credentials via properly restricted files outside Git and verify the backup role can only read its intended schema.
4. Run syntax/lint checks first. Test successful backup, invalid credential, corrupted dump/checksum, and failed storage access with synthetic data.
5. Execute append-only canary only on a throwaway repository after validating that the backup role lacks deletion rights. The script's attempted `forget` is **potentially destructive if misconfigured**.
6. A real isolated DB restore, recovery point and recovery time verification require additional scripts and evidence; `pg_restore --list` by itself is not a recovery drill.

## Deliberately excluded
- `restic-maintenance.sh`, which runs retention `forget/prune`, was not imported.
- Full DB restore scripts that can create/drop database objects were not imported. Preserve them in the source backup pending an independent non-destructive redesign.
- systemd automation and runtime endpoints were omitted until the isolated lab is reproducible.

## Provenance
Selected from `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `applications/internal-iaas-portal/backup/`. Minimal adjustment only adds a safety gate to the append-only negative test.
