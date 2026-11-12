-- NON-PRODUCTION EXAMPLE: policy illustration only. Do not execute this file.
-- Password material is represented only by an external-management placeholder.
-- Applications never use root. Remote root login is denied; no remote root account is defined.
-- Wildcard host scope is intentionally absent.

CREATE USER IF NOT EXISTS '<application-db-user>'@'<database-client-subnet>'
  IDENTIFIED BY '<secure-password-managed-outside-repository>';
GRANT SELECT, INSERT, UPDATE, DELETE ON `<application-database>`.*
  TO '<application-db-user>'@'<database-client-subnet>';

CREATE USER IF NOT EXISTS '<replication-db-user>'@'<database-cidr>'
  IDENTIFIED BY '<secure-password-managed-outside-repository>';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.*
  TO '<replication-db-user>'@'<database-cidr>';

CREATE USER IF NOT EXISTS '<monitoring-db-user>'@'<database-client-subnet>'
  IDENTIFIED BY '<secure-password-managed-outside-repository>';
GRANT SELECT ON `performance_schema`.*
  TO '<monitoring-db-user>'@'<database-client-subnet>';

-- Administrative identity is declared separately; its grants require a distinct approved workflow.
CREATE USER IF NOT EXISTS '<admin-db-user>'@'<management-database-subnet>'
  IDENTIFIED BY '<secure-password-managed-outside-repository>';

