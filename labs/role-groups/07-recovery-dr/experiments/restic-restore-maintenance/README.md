# Lab 48: Restic Restore, Maintenance & Scheduled Backups

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. The remaining **19 source files** under the former IDP backup and recovery trees were copied, excluding files already preserved by [Lab 20](../postgres-restic-verification/README.md).

## Why separate?
Lab 20 covers logical backup and snapshot evidence checks. This lab preserves the **restore, retention, append-only credential controls and scheduling** examples, which require stronger safety boundaries and a separate disaster recovery test environment.

## Included
- `reference/recovery/`: restore and verification scripts (potentially create/drop databases on failed restores).
- `reference/backup/scripts/`: Restic maintenance with `forget` and `prune` calls.
- `reference/backup/systemd/`: backup/verification/maintenance service and timer examples.
- `reference/backup/verification/` and `reference/backup/restic/`: credential denial check and separate maintenance configuration.
- Original `.sh`, `.service` and `.timer` files were intentionally renamed to `.reference.txt`. **Do not execute or install them unchanged.**

## Independent lab gates
1. Create a throwaway PostgreSQL + Restic repository with a uniquely named restore DB and **no production routes**.
2. Verify all credentials, storage isolation, snapshots, retention and append-only denial.
3. Run intentional failures, with strict guards against deleting existing data or clobbering an active restore.
4. Validate a successful isolated restore, checksum comparison, repeated operation, measured RPO/RTO, and scheduled maintenance separation.
5. Only after manual safety review implement a new runnable lab script. No inherited destructive commands are authorized here.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No restore, forget, prune or systemd actions were executed.
