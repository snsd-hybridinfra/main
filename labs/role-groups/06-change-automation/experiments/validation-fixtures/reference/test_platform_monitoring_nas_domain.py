import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_monitoring_assistant_is_bounded_and_non_authoritative() -> None:
    contract = load_json("docs/platform/monitoring-ml-assistant.yaml")
    assert contract["status"] == "IMPLEMENTED_LOCAL"
    assert contract["runtime_validation_status"] == "NOT_VALIDATED"
    assert set(contract["identity"]["required_scopes"]) == {"llm:invoke", "monitoring:assist"}
    assert contract["identity"]["personal_chatgpt_session_allowed"] is False
    assert contract["provider"]["default"] == "DISABLED"
    assert contract["provider"]["request_storage"] is False
    assert contract["authority"]["output"] == "ADVISORY_ONLY"
    assert contract["authority"]["human_review_required"] is True
    for capability in ("may_change_detection_state", "may_approve", "may_block", "may_remediate"):
        assert contract["authority"][capability] is False
    prohibited = set(contract["input_contract"]["prohibited"])
    assert {"RAW_LOG", "FREE_FORM_PROMPT", "FILE_CONTENT", "SECRET", "IP_ADDRESS", "USER_ID"} <= prohibited


def test_nas_exchange_reuses_existing_products_without_cross_zone_write() -> None:
    exchange = load_json("docs/platform/nas-file-exchange.yaml")
    catalog = load_json("docs/platform/composite-service-catalog.yaml")
    assert exchange["status"] == "IMPLEMENTED_LOCAL_SIMULATION"
    assert exchange["runtime_validation_status"] == "NOT_VALIDATED"
    assert exchange["local_simulation"]["file_bytes_accessed"] is False
    assert exchange["local_simulation"]["nas_mount_performed"] is False
    assert exchange["local_simulation"]["runtime_credit"] == "NONE"
    assert exchange["scanner_contract"]["prohibited_inputs"] == [
        "FILENAME", "FILE_CONTENT", "RAW_SCANNER_OUTPUT", "USER_NAME", "IP_ADDRESS", "SECRET"
    ]
    assert exchange["scanner_contract"]["self_approval_allowed"] is False
    assert exchange["scanner_contract"]["reviewer_mfa_required"] is True
    assert exchange["topology"]["shared_writable_mount_across_zones"] is False
    assert exchange["protocol"] == {
        "allowed": ["SMB_3_1_1"],
        "encryption_required": True,
        "signing_required": True,
        "smb1_enabled": False,
        "smb2_enabled": False,
        "public_internet_exposure": False,
    }
    assert exchange["monitoring"]["llm_file_content_access"] is False
    assert len(catalog["blueprints"]) == 8
    nas = next(item for item in catalog["components"] if item["component_id"] == "NAS_FILE_EXCHANGE")
    assert nas["user_visible"] is False
    bound = {item["blueprint_id"] for item in catalog["blueprints"] if "NAS_FILE_EXCHANGE" in item["components"]}
    assert bound == {"API_DEVELOPMENT_STACK", "DATA_PROCESSING_LAB"}
    assert "NAS_FILE_EXCHANGE" not in catalog["allowed_user_inputs"]


def test_final_frontend_domain_is_exact_and_runtime_unvalidated() -> None:
    contract = load_json("docs/platform/frontend-domain.yaml")
    assert contract["runtime_validation_status"] == "NOT_VALIDATED"
    assert contract["ownership"]["dns_proof_collected"] is False
    assert contract["origins"] == {
        "user_portal": "https://gg-snsdinfra.cloud",
        "admin_portal": "https://admin.gg-snsdinfra.cloud",
        "identity": "https://id.gg-snsdinfra.cloud",
    }
    deployment = (ROOT / "applications/internal-iaas-portal/kubernetes/edge-gateway/deployment.yaml").read_text(encoding="utf-8")
    request_config = (ROOT / "applications/internal-iaas-portal/kubernetes/request-api/configmap.yaml").read_text(encoding="utf-8")
    for host in ("gg-snsdinfra.cloud", "admin.gg-snsdinfra.cloud", "id.gg-snsdinfra.cloud"):
        assert host in deployment
    assert contract["oidc"]["issuer"] in request_config
