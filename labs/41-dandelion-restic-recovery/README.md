# Lab 41: Dandelion Restic Backup and Recovery Scenarios

**State:** `SOURCE_EXTRACTED / NOT_REVALIDATED`.

## Goal
Derive a reproducible, isolated backup/restore exercise from **Team Dandelion's** OpenStack WordPress, MariaDB, HAProxy and Prometheus design.

## References
- `reference/operations/backup-recovery-scenario-routines.md`: five scoped restoration scenarios
- `reference/operations/dandelion-restic-backup.sh.reference.txt`: **historical script, not safe to execute**. Contains remote SSH operations, destructive cleanup in staging, container volume archiving and DB dump commands. May not work as written.
- `reference/operations/dandelion-restic-restore-test.sh.reference.txt`: **historical script, not safe to execute**. Empties a fixed restore-test directory before restoring.
- `reference/operations/backup-vars-example.yml`: sanitized example: old private IPs and demonstration password replaced.
- `reference/backup-recovery-plan.md`: original plan/actual vs planned scope descriptions.

## Verification plan
1. Build synthetic WordPress volume, MariaDB test data, HAProxy example config and a disposable Restic repository.
2. Implement a **new dry-run-by-default** backup script using configurable temporary directories. Avoid deleting inherited system paths or connecting to old hosts.
3. Test file checksums, snapshot creation, corrupted backup rejection, isolated restoration and automated recovery approval separation.
4. Collect RPO/RTO only when actual timed restore tests succeed; a plan alone proves nothing.
5. Compare approach with [Lab 20 PostgreSQL/Restic](../20-postgres-restic-verification/README.md) and [Lab 36 Day-2 Runbooks](../36-day2-operations-runbooks/README.md).

## Provenance
Reused Team Dandelion material from `snsd-hybridinfra/dandelion-cloud-automation` commit `22a21c02973e696a9a07c91da3bc2ea033881ea6`. Source team attribution and original commit history stay in the source repo. Redistribution/individual contribution must not be misrepresented. No commands have been run.


## Additional historical backup scripts
`reference/scripts/backup*.reference.txt` and `reference/scripts/backup/*.reference.txt` preserve four older Team Dandelion backup scripts as **non-executable historical references**. Review fixed paths, SSH access and overwrite risks before constructing a new test-only implementation.
