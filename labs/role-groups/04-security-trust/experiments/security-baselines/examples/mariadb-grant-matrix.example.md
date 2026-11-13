# MariaDB Grant Matrix Example

NON-PRODUCTION EXAMPLE: this matrix documents policy placeholders and is not a live grant inventory.

| Account Placeholder | Host Scope Placeholder | Database Scope | Allowed Privileges | Explicitly Forbidden Privileges | Purpose | Least Privilege Judgment | Evidence Reference |
|---|---|---|---|---|---|---|---|
| `<application-db-user>` | `<internal-service-cidr>` | `<application-database>` | SELECT, INSERT, UPDATE, DELETE | SUPER, FILE, PROCESS, SHUTDOWN, RELOAD, CREATE USER, GRANT OPTION, ALL PRIVILEGES | Application DML only; never root | PASS | retired-numbered-case |
| `<replication-db-user>` | `<database-cidr>` | replication channel placeholder | REPLICATION SLAVE, REPLICATION CLIENT | SUPER, FILE, PROCESS, SHUTDOWN, RELOAD, CREATE USER, GRANT OPTION, ALL PRIVILEGES | Primary-replica transport only | PASS | retired-numbered-case |
| `<monitoring-db-user>` | `<database-client-subnet>` | metadata/status schemas | SELECT and read-only status-related access | SUPER, FILE, PROCESS, SHUTDOWN, RELOAD, CREATE USER, GRANT OPTION, ALL PRIVILEGES | Read-only monitoring | PASS | retired-numbered-case |
| `<admin-db-user>` | `<management-database-subnet>` | administration boundary placeholder | Separately approved administrative workflow | Application credential reuse | Administrative identity separated from application identity | REVIEW_REQUIRED | retired-numbered-case |

## Account Rules

- Application and monitoring accounts must not receive `ALL PRIVILEGES` or `GRANT OPTION`.
- The application identity must never use root.
- Remote root login is denied.
- Host scope uses private placeholders such as `<internal-service-cidr>` or `<database-client-subnet>`, never an unrestricted real value.
