# MariaDB Access Control Baseline

This repository-side baseline is a non-production policy model. It does not connect to or configure MariaDB.

## Least Privilege Database Access Principle

- Every database account is separated by operational purpose and receives only the minimum required privilege.
- `<application-db-user>` may receive required DML privileges on `<application-database>` only.
- The application user must not have `SUPER`, `FILE`, `PROCESS`, `SHUTDOWN`, `RELOAD`, `CREATE USER`, `GRANT OPTION`, or `ALL PRIVILEGES`.
- `<replication-db-user>` may receive only replication-related privileges for `<db-primary-host>` and `<db-replica-host>` workflows.
- `<monitoring-db-user>` receives read-only metadata/status access only and no administrative or grant privilege.
- `<admin-db-user>` is separated from the application, replication, and monitoring identities.
- The root account must not be used by applications.
- Remote root login must be denied.
- Wildcard host `%` must be avoided; any placeholder exception is a documented risk and not a baseline approval.
- Database access is restricted to `<internal-service-cidr>` or `<database-cidr>` on the private internal service network.
- Passwords must not be stored in repository files and must be managed outside this repository.

## Evidence Collection Model

- Run the local validator without a database client or network access.
- Store the generated log and summary below `<evidence-path>`.
- Record checks using stable IDs and sanitized repository paths.
- Reject real credentials, connection strings, dumps, addresses, private material, and account-specific content.

