\set ON_ERROR_STOP on

REVOKE ALL ON DATABASE identity_db FROM PUBLIC;
GRANT CONNECT ON DATABASE identity_db TO keycloak_app, identity_backup, identity_auditor;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA keycloak FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA keycloak TO keycloak_app;
GRANT USAGE ON SCHEMA keycloak TO identity_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA keycloak TO identity_backup;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA keycloak TO identity_backup;

ALTER DEFAULT PRIVILEGES FOR ROLE keycloak_app IN SCHEMA keycloak
    GRANT SELECT ON TABLES TO identity_backup;
ALTER DEFAULT PRIVILEGES FOR ROLE keycloak_app IN SCHEMA keycloak
    GRANT USAGE, SELECT ON SEQUENCES TO identity_backup;

REVOKE ALL ON DATABASE identity_db FROM request_app, approval_app, grant_app;
REVOKE CREATE ON SCHEMA keycloak FROM identity_backup, identity_auditor;
