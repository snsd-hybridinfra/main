from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_user_portal_exposes_complete_mvp_story() -> None:
    html = read("services/user-portal/index.html")
    script = read("services/user-portal/assets/app.js")

    for element_id in (
        'id="login-view"',
        'id="catalog"',
        'id="request-form"',
        'id="product-parameters"',
        'id="requests"',
        'id="resources"',
        'id="monitoring"',
        'id="request-detail-dialog"',
        'id="last-refreshed"',
    ):
        assert element_id in html

    for blueprint_id in (
        "DEVELOPER_WORKSPACE",
        "SECURE_ADMIN_WORKSPACE",
        "WEB_APPLICATION_STACK",
        "API_DEVELOPMENT_STACK",
        "VM_APPLICATION_STACK",
        "AI_AGENT_SANDBOX",
        "DATA_PROCESSING_LAB",
        "SYNTHETIC_MARKET_DATA_LAB",
    ):
        assert blueprint_id in script
    for internal_profile in (
        "DEV-OS-VM-S",
        "DEV-OS-VM-M",
        "DEV-OS-VM-L",
        "DEV-OS-K3S-S",
        "DEV-OS-K3S-M",
    ):
        assert internal_profile not in script
    for retired_product in (
        "kubernetes-namespace",
        "postgresql-dev-db",
        "internal-api-access",
        "grafana-viewer",
    ):
        assert retired_product not in script

    assert "statusTimeline" in script
    assert 'aria-label="사용자 포털 메뉴"' in html
    for anchor in ("#user-overview", "#user-catalog", "#request-section", "#user-requests", "#user-resources", "#user-monitoring"):
        assert f'href="{anchor}"' in html
    assert "DEMO 샘플 데이터" in html
    assert "/auth/user/login" in script
    assert "/api/v1/blueprint-requests" in script
    assert "/api/v1/resources" in script
    assert "window.setInterval" in script
    assert "if (refreshCatalog || catalog.length === 0) loaders.unshift(loadCatalog())" in script
    assert "refreshAll({refreshCatalog: true})" in script
    assert "<th>신청 ID</th>" not in script
    assert "<dt>Grant ID</dt>" not in script
    assert 'name="environment"' in script
    assert 'name="size"' in script
    assert "resource-details" in script
    assert 'name="duration_hours"' in html
    assert '<option value="4">4시간</option>' in html
    assert '<option value="8">8시간</option>' in html
    assert '<option value="24" selected>1일</option>' in html
    assert '<option value="72">3일</option>' in html
    assert '<option value="168">7일</option>' in html
    assert "allowed_duration_hours" in script
    assert 'name="cpu"' not in html
    assert 'name="memory_gib"' not in html
    assert 'name="storage_gib"' not in html
    assert "모니터링은 별도 신청 없이" in html
    assert "apiErrorMessage" in script
    assert "<strong>자원 사용</strong>" in html
    assert "<strong>회수·만료</strong>" in html


def test_admin_portal_exposes_control_and_audit_story() -> None:
    html = read("services/admin-portal/index.html")
    script = read("services/admin-portal/assets/app.js")

    for element_id in (
        'id="login-view"',
        'id="requests"',
        'id="sync-status"',
        'id="provisioning-jobs"',
        'id="grants"',
        'id="monitoring-dashboard"',
        'id="monitoring-state"',
        'id="request-detail-dialog"',
        'id="sync-failed-count"',
        'id="last-refreshed"',
        'id="reset-demo"',
        'id="admin-demo"',
        'id="seed-demo"',
    ):
        assert element_id in html

    assert "DEMO 샘플 데이터" in html
    assert 'aria-label="관리자 포털 메뉴"' in html
    for anchor in ("#admin-overview", "#admin-demo", "#admin-requests", "#admin-sync", "#admin-provisioning", "#admin-grants", "#admin-monitoring"):
        assert f'href="{anchor}"' in html
    assert "/auth/admin/login" in script
    assert "/admin-api/v1/requests?status=ALL" in script
    assert "/retry-sync" in script
    assert "/admin-api/v1/grants?status=ALL" in script
    assert "/admin-api/v1/provisioning/jobs?status=ALL" in script
    assert "/admin-api/v1/monitoring-dashboard" in script
    assert "/admin-api/v1/audit-events" not in script
    assert "/admin-api/v1/grant-audit-events" not in script
    assert "/admin-api/v1/demo/reset" in script
    assert "/admin-api/v1/demo/seed" in script
    assert "/expire-now" in script
    assert "apiErrorMessage" in script
    assert "confirm(" in script
    assert "window.setInterval" in script
    assert "<th>Grant ID</th>" not in script
    assert "<dt>신청 ID</dt>" not in script
