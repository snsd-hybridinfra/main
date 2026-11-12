\set ON_ERROR_STOP on

DO $verify$
BEGIN
    IF has_schema_privilege('approval_app', 'control_service', 'CREATE') OR
       has_schema_privilege('grant_app', 'control_service', 'CREATE') THEN
        RAISE EXCEPTION 'application role unexpectedly has CREATE on control_service';
    END IF;
    IF NOT has_table_privilege('approval_app', 'control_service.approval_requests', 'SELECT,INSERT,UPDATE,DELETE') THEN
        RAISE EXCEPTION 'approval_app DML grant is incomplete';
    END IF;
    IF NOT has_table_privilege('approval_app', 'control_service.provisioning_jobs', 'SELECT,INSERT,UPDATE,DELETE') THEN
        RAISE EXCEPTION 'approval_app provisioning job grant is incomplete';
    END IF;
    IF has_table_privilege('approval_app', 'control_service.grants', 'SELECT') THEN
        RAISE EXCEPTION 'approval_app unexpectedly reads grants';
    END IF;
    IF NOT has_table_privilege('grant_app', 'control_service.grants', 'SELECT,INSERT,UPDATE,DELETE') THEN
        RAISE EXCEPTION 'grant_app DML grant is incomplete';
    END IF;
    IF has_table_privilege('grant_app', 'control_service.approval_requests', 'SELECT') THEN
        RAISE EXCEPTION 'grant_app unexpectedly reads approval requests';
    END IF;
    IF has_table_privilege('grant_app', 'control_service.provisioning_jobs', 'SELECT') THEN
        RAISE EXCEPTION 'grant_app unexpectedly reads provisioning jobs';
    END IF;
    IF has_table_privilege('control_backup', 'control_service.grants', 'INSERT') THEN
        RAISE EXCEPTION 'control_backup unexpectedly has INSERT';
    END IF;
    IF NOT has_table_privilege('control_auditor', 'control_service.audit_events', 'SELECT') THEN
        RAISE EXCEPTION 'control_auditor lacks audit SELECT';
    END IF;
END
$verify$;

SELECT 'control permissions: PASS' AS result;
