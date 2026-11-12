\set ON_ERROR_STOP on

REVOKE ALL ON DATABASE control_db FROM PUBLIC;
GRANT CONNECT ON DATABASE control_db TO control_migrator, approval_app, grant_app, control_backup, control_auditor;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA IF NOT EXISTS control_service AUTHORIZATION control_migrator;
REVOKE ALL ON SCHEMA control_service FROM PUBLIC;
GRANT USAGE ON SCHEMA control_service TO approval_app, grant_app, control_backup, control_auditor;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    control_service.approval_requests,
    control_service.approval_decisions,
    control_service.provisioning_jobs,
    control_service.audit_events
TO approval_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    control_service.grants,
    control_service.audit_events
TO grant_app;

GRANT SELECT ON ALL TABLES IN SCHEMA control_service TO control_backup;
GRANT SELECT ON control_service.audit_events TO control_auditor;

ALTER DEFAULT PRIVILEGES FOR ROLE control_migrator IN SCHEMA control_service
    GRANT SELECT ON TABLES TO control_backup;

REVOKE CREATE ON SCHEMA control_service FROM approval_app, grant_app, control_backup, control_auditor;
REVOKE ALL ON control_service.grants FROM approval_app;
REVOKE ALL ON control_service.approval_requests, control_service.approval_decisions, control_service.provisioning_jobs FROM grant_app;
