\set ON_ERROR_STOP on

REVOKE ALL ON DATABASE request_db FROM PUBLIC;
GRANT CONNECT ON DATABASE request_db TO request_migrator, request_app, request_backup, request_auditor;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA IF NOT EXISTS request_service AUTHORIZATION request_migrator;
REVOKE ALL ON SCHEMA request_service FROM PUBLIC;
GRANT USAGE ON SCHEMA request_service TO request_app, request_backup, request_auditor;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA request_service TO request_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA request_service TO request_app;
GRANT SELECT ON ALL TABLES IN SCHEMA request_service TO request_backup, request_auditor;

ALTER DEFAULT PRIVILEGES FOR ROLE request_migrator IN SCHEMA request_service
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO request_app;
ALTER DEFAULT PRIVILEGES FOR ROLE request_migrator IN SCHEMA request_service
    GRANT USAGE, SELECT ON SEQUENCES TO request_app;
ALTER DEFAULT PRIVILEGES FOR ROLE request_migrator IN SCHEMA request_service
    GRANT SELECT ON TABLES TO request_backup, request_auditor;

REVOKE CREATE ON SCHEMA request_service FROM request_app, request_backup, request_auditor;
