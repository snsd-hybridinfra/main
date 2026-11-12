\set ON_ERROR_STOP on

DO $verify$
BEGIN
    IF has_database_privilege('request_app', 'identity_db', 'CONNECT') OR
       has_database_privilege('approval_app', 'identity_db', 'CONNECT') OR
       has_database_privilege('grant_app', 'identity_db', 'CONNECT') THEN
        RAISE EXCEPTION 'service API role unexpectedly connects to identity_db';
    END IF;
    IF NOT has_schema_privilege('keycloak_app', 'keycloak', 'USAGE,CREATE') THEN
        RAISE EXCEPTION 'keycloak_app schema privileges are incomplete';
    END IF;
    IF has_schema_privilege('identity_backup', 'keycloak', 'CREATE') THEN
        RAISE EXCEPTION 'identity_backup unexpectedly creates identity objects';
    END IF;
END
$verify$;

SELECT 'identity permissions: PASS' AS result;
