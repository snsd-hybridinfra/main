\set ON_ERROR_STOP on

-- Passwords are intentionally not set here. Provision LOGIN credentials through
-- the approved secret workflow after these roles exist.
DO $roles$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY[
        'request_migrator', 'request_app', 'request_backup', 'request_auditor',
        'control_migrator', 'approval_app', 'grant_app', 'control_backup', 'control_auditor',
        'keycloak_app', 'identity_backup', 'identity_auditor'
    ] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
            EXECUTE format(
                'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
                role_name
            );
        END IF;
    END LOOP;
END
$roles$;

ALTER ROLE request_migrator SET search_path = request_service, pg_catalog;
ALTER ROLE request_app SET search_path = request_service, pg_catalog;
ALTER ROLE request_backup SET search_path = request_service, pg_catalog;
ALTER ROLE request_auditor SET search_path = request_service, pg_catalog;
ALTER ROLE control_migrator SET search_path = control_service, pg_catalog;
ALTER ROLE approval_app SET search_path = control_service, pg_catalog;
ALTER ROLE grant_app SET search_path = control_service, pg_catalog;
ALTER ROLE control_backup SET search_path = control_service, pg_catalog;
ALTER ROLE control_auditor SET search_path = control_service, pg_catalog;
ALTER ROLE keycloak_app SET search_path = keycloak, pg_catalog;
ALTER ROLE identity_backup SET search_path = keycloak, pg_catalog;
ALTER ROLE identity_auditor SET search_path = pg_catalog;

ALTER ROLE request_app SET statement_timeout = '15s';
ALTER ROLE approval_app SET statement_timeout = '15s';
ALTER ROLE grant_app SET statement_timeout = '15s';
ALTER ROLE keycloak_app SET statement_timeout = '30s';
ALTER ROLE request_app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE approval_app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE grant_app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE keycloak_app SET idle_in_transaction_session_timeout = '30s';
