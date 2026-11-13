BEGIN;

REVOKE ALL ON DATABASE identity_db FROM PUBLIC;
GRANT CONNECT ON DATABASE identity_db TO keycloak_app, identity_backup, identity_auditor;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA IF NOT EXISTS keycloak AUTHORIZATION keycloak_app;
REVOKE ALL ON SCHEMA keycloak FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA keycloak TO keycloak_app;
GRANT USAGE ON SCHEMA keycloak TO identity_backup;

ALTER DEFAULT PRIVILEGES FOR ROLE keycloak_app IN SCHEMA keycloak
    GRANT SELECT ON TABLES TO identity_backup;
ALTER DEFAULT PRIVILEGES FOR ROLE keycloak_app IN SCHEMA keycloak
    GRANT USAGE, SELECT ON SEQUENCES TO identity_backup;

-- Keycloak creates and migrates its own tables. Application APIs never receive
-- CONNECT or USAGE grants on this database/schema.
REVOKE ALL ON DATABASE identity_db FROM request_app, approval_app, grant_app;

COMMIT;
