"""Exercise the image filesystem layout without a source checkout on sys.path."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2]
ROOT = APP.parents[1]


def test_shallow_image_path_uses_packaged_authorities():
    from request_api.blueprints import _authority_paths
    module_file = Path("/app/request_api/blueprints.py")
    assert _authority_paths(module_file) == (
        module_file.parent / "authorities/composite-service-catalog.yaml",
        module_file.parent / "authorities/catalog.json")


@pytest.mark.parametrize("catalog_state", ["valid", "missing", "tampered"])
def test_packaged_api_preserves_catalog_authority(tmp_path, catalog_state):
    package = tmp_path / "request_api"
    shutil.copytree(APP / "services/request-api/request_api", package,
                    ignore=shutil.ignore_patterns("__pycache__"))
    authorities = package / "authorities"
    authorities.mkdir()
    shutil.copyfile(APP / "terraform/catalog.json", authorities / "catalog.json")
    if catalog_state != "missing":
        catalog = json.loads((ROOT / "docs/platform/composite-service-catalog.yaml").read_text(encoding="utf-8"))
        if catalog_state == "tampered":
            catalog["construction_policy"]["arbitrary_hcl"] = True
        (authorities / "composite-service-catalog.yaml").write_text(json.dumps(catalog), encoding="utf-8")
    script = '''
from fastapi.testclient import TestClient
from request_api.main import create_app
from request_api.config import Settings
import sys
app = create_app(Settings(database_url="sqlite+pysqlite:///packaged-test.db", auto_create_schema=True, auth_mode="dev"))
headers = {"X-Dev-User":"package-test", "X-Dev-Roles":"CUSTOMER_USER", "X-Dev-Tenant":"package-tenant",
           "X-Dev-Scopes":"developer:read cloud:read"}
with TestClient(app) as client:
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == (200 if sys.argv[1] == "valid" else 503)
    response = client.get("/api/developer/workspace", headers=headers)
    if sys.argv[1] == "valid":
        assert response.status_code == 200, response.text
        items = response.json()["catalog"]
        assert len(items) == 8
        assert {i["blueprint_id"] for i in items if i["requestable"]} == {"VM_APPLICATION_STACK"}
        assert all(i["runtime_evidence"] == "NOT_VALIDATED" for i in items)
    else:
        assert response.status_code == 503, response.text
'''
    environment = {**os.environ, "PYTHONPATH": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, "-c", script, catalog_state], cwd=tmp_path,
                            env=environment, text=True, capture_output=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
