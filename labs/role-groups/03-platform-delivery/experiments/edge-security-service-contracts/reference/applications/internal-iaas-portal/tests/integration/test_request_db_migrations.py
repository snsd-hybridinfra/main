"""Opt-in PostgreSQL 16 test: private disposable container, no published ports."""
import io
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

APP = Path(__file__).resolve().parents[2]
MIGRATIONS = APP / "database/migrations/request-db"


def test_postgres16_upgrade_rollback_and_request_preservation(monkeypatch):
    image = os.getenv("IDP_TEST_POSTGRES_IMAGE", "")
    if not image:
        pytest.skip("Set IDP_TEST_POSTGRES_IMAGE to an existing official PostgreSQL 16 digest")
    assert re.fullmatch(r"postgres@sha256:[0-9a-f]{64}", image), "an immutable official image reference is required"
    docker = shutil.which("docker")
    assert docker, "Docker is required for the explicitly enabled migration test"

    def execute(*args, sql=None, require_success=True):
        result = subprocess.run([docker, *args], input=sql, text=True, encoding="utf-8", capture_output=True, timeout=60)
        if require_success:
            assert result.returncode == 0, result.stderr
        return result

    # Inspect only: this test never downloads an image or contacts a database URL.
    execute("image", "inspect", image)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://offline.invalid/migration_fixture")

    def render(direction, revision):
        buffer = io.StringIO()
        config = Config(str(MIGRATIONS / "alembic.ini"), output_buffer=buffer)
        getattr(command, direction)(config, revision, sql=True)
        return buffer.getvalue()

    up = render("upgrade", "head")
    down = render("downgrade", "head:0005_agent_budget_trace")
    restore = render("upgrade", "0005_agent_budget_trace:head")
    container = None
    try:
        container = execute("create", "--name", "snsd-migration-test-" + uuid4().hex,
            "--label", "snsd.local-test=request-db-migration", "--network", "none",
            "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
            "--tmpfs", "/var/lib/postgresql/data",
            "--env", "POSTGRES_DB=request_db",
            "--env", "POSTGRES_PASSWORD=" + uuid4().hex, image).stdout.strip()
        execute("start", container)
        deadline = time.monotonic() + 30
        while execute("exec", container, "pg_isready", "-U", "postgres", require_success=False).returncode:
            assert time.monotonic() < deadline, "disposable PostgreSQL did not become ready"
            time.sleep(0.2)

        def sql(value, require_success=True, user="postgres"):
            return execute("exec", "-i", container, "psql", "-X", "-U", user, "-d", "request_db",
                           "-v", "ON_ERROR_STOP=1", "-At", sql=value, require_success=require_success)

        version = sql("SHOW server_version;").stdout.strip()
        assert version.startswith("16."), version
        sql((APP / "database/roles/00-create-roles.sql").read_text(encoding="utf-8"))
        sql("ALTER DATABASE request_db OWNER TO request_migrator;")
        sql(up, user="request_migrator")
        sql((APP / "database/roles/10-request-db-grants.sql").read_text(encoding="utf-8"))
        sql((APP / "database/verification/verify-request-permissions.sql").read_text(encoding="utf-8"))
        assert sql("SELECT version_num FROM request_service.alembic_version;").stdout.strip() == "0006_portal_usage"
        sql("""INSERT INTO request_service.access_requests
            (request_id,idempotency_key,owner_id,product_code,cpu,memory_gib,storage_gib,duration_hours,purpose,status)
            VALUES ('fixture-request','fixture-key','fixture-owner','DEV-OS-VM-S',2,2,30,4,'migration persistence fixture','PENDING');""", user="request_app")
        usage = """INSERT INTO request_service.portal_usage VALUES
            ('fixture-usage','fixture-meter','fixture-tenant','fixture-owner','local-simulator',5,10,now());"""
        sql(usage, user="request_app")
        duplicate = sql(usage.replace("fixture-usage", "second-usage"), require_success=False, user="request_app")
        assert duplicate.returncode != 0 and "unique constraint" in duplicate.stderr.lower()
        denied = sql("CREATE TABLE request_service.unapproved_fixture (id integer);", require_success=False, user="request_app")
        assert denied.returncode != 0 and "permission denied" in denied.stderr.lower()
        columns = sql("SELECT column_name FROM information_schema.columns WHERE table_schema='request_service' "
                      "AND table_name='portal_usage' ORDER BY column_name;").stdout.splitlines()
        assert set(columns) == {"usage_id", "idempotency_key", "tenant_id", "owner_id", "model",
                                "input_units", "output_units", "created_at"}
        sql(down, user="request_migrator")
        assert sql("SELECT version_num FROM request_service.alembic_version;").stdout.strip() == "0005_agent_budget_trace"
        assert sql("SELECT to_regclass('request_service.portal_usage') IS NULL;").stdout.strip() == "t"
        assert sql("SELECT count(*) FROM request_service.access_requests WHERE request_id='fixture-request';").stdout.strip() == "1"
        sql(restore, user="request_migrator")
        assert sql("SELECT version_num FROM request_service.alembic_version;").stdout.strip() == "0006_portal_usage"
        sql(usage, user="request_app")
        assert sql("SELECT count(*) FROM request_service.portal_usage;").stdout.strip() == "1"
        print(f"PostgreSQL {version}: upgrade, duplicate/DDL denial, downgrade, request preservation, re-upgrade with app DML PASS")
    finally:
        if container:
            execute("rm", "--force", "--volumes", container)
