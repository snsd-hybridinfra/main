\set ON_ERROR_STOP on

DO $verify$
BEGIN
    IF has_schema_privilege('request_app', 'request_service', 'CREATE') THEN
        RAISE EXCEPTION 'request_app unexpectedly has CREATE on request_service';
    END IF;
    IF NOT has_table_privilege('request_app', 'request_service.access_requests', 'SELECT,INSERT,UPDATE,DELETE') THEN
        RAISE EXCEPTION 'request_app DML grant is incomplete';
    END IF;
    IF has_table_privilege('request_backup', 'request_service.access_requests', 'INSERT') THEN
        RAISE EXCEPTION 'request_backup unexpectedly has INSERT';
    END IF;
    IF NOT has_table_privilege('request_backup', 'request_service.access_requests', 'SELECT') THEN
        RAISE EXCEPTION 'request_backup lacks SELECT';
    END IF;
END
$verify$;

SELECT 'request permissions: PASS' AS result;
