from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _authority_paths(module_file: Path) -> tuple[Path, Path]:
    # Source runs read the canonical repository files. Images carry exact copies
    # alongside the package; never assume that /app has five parent directories.
    parents = module_file.parents
    if len(parents) > 5:
        root = parents[5]
        source = root / "applications/internal-iaas-portal/services/request-api/request_api/blueprints.py"
        if module_file == source:
            return (root / "docs/platform/composite-service-catalog.yaml",
                    root / "applications/internal-iaas-portal/terraform/catalog.json")
    packaged = module_file.parent / "authorities"
    return packaged / "composite-service-catalog.yaml", packaged / "catalog.json"


COMPOSITE_CATALOG_PATH, EXECUTION_PROFILE_PATH = _authority_paths(Path(__file__).resolve())

EXPECTED_EXECUTION_PROFILES = {
    "DEV-OS-VM-S",
    "DEV-OS-VM-M",
    "DEV-OS-VM-L",
    "DEV-OS-K3S-S",
    "DEV-OS-K3S-M",
}
POLICY_COMPONENTS = {"NETWORK_POLICY", "OPERATIONS_PROFILE"}
PROFILE_COMPONENTS = {"COMPUTE_VM", "K3S_RUNTIME"}
PURPOSE_PATTERN = re.compile(r"^[^\x00-\x1f\x7f]{5,200}$")

PROFILE_BY_BLUEPRINT_SIZE: dict[str, dict[str, str]] = {
    "WEB_APPLICATION_STACK": {
        "SMALL": "DEV-OS-K3S-S",
        "STANDARD": "DEV-OS-K3S-M",
    },
    "API_DEVELOPMENT_STACK": {
        "SMALL": "DEV-OS-K3S-S",
        "STANDARD": "DEV-OS-K3S-M",
    },
    "VM_APPLICATION_STACK": {
        "SMALL": "DEV-OS-VM-S",
        "STANDARD": "DEV-OS-VM-M",
        "LARGE": "DEV-OS-VM-L",
    },
    "AI_AGENT_SANDBOX": {
        "STANDARD": "DEV-OS-K3S-S",
        "LARGE": "DEV-OS-K3S-M",
    },
    "DATA_PROCESSING_LAB": {
        "STANDARD": "DEV-OS-VM-M",
        "LARGE": "DEV-OS-VM-L",
    },
    "SYNTHETIC_MARKET_DATA_LAB": {"STANDARD": "DEV-OS-K3S-M"},
}
BLUEPRINT_RUNTIME_GATES: dict[str, list[str]] = {
    "API_DEVELOPMENT_STACK": [
        "K3S_TENANT_BASELINE",
        "APPROVED_INTERNAL_REGISTRY",
        "OIDC_AND_RBAC",
        "EXTERNAL_SECRET_MANAGER",
        "POSTGRESQL_ADAPTER",
        "REDIS_ADAPTER",
        "MESSAGE_QUEUE_ADAPTER",
        "OBJECT_STORAGE_ADAPTER",
        "NAS_FILE_EXCHANGE_ADAPTER",
        "PRIVATE_INGRESS_ADAPTER",
        "OTEL_PIPELINE",
    ],
    "AI_AGENT_SANDBOX": [
        "SANDBOX_RUNTIME_CLASS",
        "TASK_CREDENTIAL_BROKER",
        "FQDN_EGRESS_BROKER",
        "AGENT_BUDGET_ENFORCER",
        "APPROVAL_RESUME_CONTROLLER",
        "SANITIZED_TRACE_PIPELINE",
    ]
}


class BlueprintResolutionError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BlueprintResolutionError(f"catalog authority cannot be loaded: {path.name}") from exc
    if not isinstance(data, dict):
        raise BlueprintResolutionError(f"catalog authority must be an object: {path.name}")
    return data


def load_authorities() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = _load_json(COMPOSITE_CATALOG_PATH)
    profiles = _load_json(EXECUTION_PROFILE_PATH)
    policy = catalog.get("construction_policy", {})
    required_policy = {
        "components_user_selectable": False,
        "free_form_composition": False,
        "arbitrary_hcl": False,
        "raw_provider_identifiers": False,
        "blueprint_selection_only": True,
        "resolved_manifest_immutable": True,
        "deployment_transaction": "ALL_OR_NOTHING",
        "rollback_order": "REVERSE_DEPENDENCY_ORDER",
    }
    if catalog.get("model") != "APPROVED_COMPOSITE_BLUEPRINTS" or any(
        policy.get(key) != value for key, value in required_policy.items()
    ):
        raise BlueprintResolutionError("composite catalog construction policy is invalid")
    if set(catalog.get("allowed_user_inputs", [])) != {
        "blueprint_id",
        "environment",
        "size",
        "duration_hours",
        "purpose",
    }:
        raise BlueprintResolutionError("composite catalog user-input boundary is invalid")
    if set(profiles.get("products", {})) != EXPECTED_EXECUTION_PROFILES:
        raise BlueprintResolutionError("execution-profile catalog differs from the approved set")
    return catalog, profiles


def public_blueprints() -> list[dict[str, Any]]:
    catalog, _ = load_authorities()
    return [
        {
            "blueprint_id": item["blueprint_id"],
            "display_name": item["display_name"],
            "summary": item["user_summary"],
            "business_domain_profiles": list(item.get("business_domain_profiles", [])),
            "network_profile": item["network_profile"],
            "allowed_environments": list(item["allowed_environments"]),
            "allowed_sizes": list(item["allowed_sizes"]),
            "allowed_duration_hours": list(item["allowed_duration_hours"]),
        }
        for item in catalog.get("blueprints", [])
    ]


def canonical_manifest_digest(manifest: dict[str, Any]) -> str:
    encoded = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def resolve_blueprint(
    *,
    blueprint_id: str,
    environment: str,
    size: str,
    duration_hours: int,
    purpose: str,
) -> dict[str, Any]:
    catalog, profiles = load_authorities()
    blueprints = {
        item.get("blueprint_id"): item
        for item in catalog.get("blueprints", [])
        if isinstance(item, dict)
    }
    blueprint = blueprints.get(blueprint_id)
    if blueprint is None:
        raise BlueprintResolutionError("unknown blueprint_id")
    if environment not in blueprint.get("allowed_environments", []):
        raise BlueprintResolutionError("environment is not allowed for this blueprint")
    if size not in blueprint.get("allowed_sizes", []):
        raise BlueprintResolutionError("size is not allowed for this blueprint")
    if duration_hours not in blueprint.get("allowed_duration_hours", []):
        raise BlueprintResolutionError("duration is not allowed for this blueprint")
    if purpose != purpose.strip() or not PURPOSE_PATTERN.fullmatch(purpose):
        raise BlueprintResolutionError("purpose must be 5-200 printable characters without outer whitespace")

    selected_profile = PROFILE_BY_BLUEPRINT_SIZE.get(blueprint_id, {}).get(size)
    if selected_profile is not None and selected_profile not in profiles["products"]:
        raise BlueprintResolutionError("resolved execution profile is not approved")

    component_plan: list[dict[str, str]] = []
    blocking_components: list[str] = []
    for component_id in blueprint["components"]:
        if component_id in POLICY_COMPONENTS:
            binding_status = "POLICY_BOUND_LOCAL"
        elif component_id in PROFILE_COMPONENTS and selected_profile is not None:
            binding_status = "EXECUTION_PROFILE_BOUND_LOCAL"
        else:
            binding_status = "ADAPTER_NOT_IMPLEMENTED"
            blocking_components.append(component_id)
        component_plan.append(
            {"component_id": component_id, "binding_status": binding_status}
        )

    blocking_gates = list(BLUEPRINT_RUNTIME_GATES.get(blueprint_id, []))
    resolution_status = (
        "BLOCKED_UNIMPLEMENTED_COMPONENTS"
        if blocking_components or blocking_gates
        else "RESOLVED_LOCAL"
    )
    manifest = {
        "schema_version": "1.0.0",
        "blueprint_id": blueprint_id,
        "environment": environment,
        "size": size,
        "duration_hours": duration_hours,
        "purpose": purpose,
        "business_domain_profiles": list(blueprint.get("business_domain_profiles", [])),
        "network_profile": blueprint["network_profile"],
        "component_plan": component_plan,
        "selected_execution_profile": selected_profile,
        "deployment_transaction": "ALL_OR_NOTHING",
        "rollback_component_order": list(reversed(blueprint["components"])),
        "resolution_status": resolution_status,
        "blocking_components": blocking_components,
        "blocking_gates": blocking_gates,
        "runtime_authorized": False,
    }
    return {**manifest, "manifest_digest": canonical_manifest_digest(manifest)}


def public_resolution(resolution: dict[str, Any]) -> dict[str, Any]:
    return {
        "blueprint_id": resolution["blueprint_id"],
        "environment": resolution["environment"],
        "size": resolution["size"],
        "duration_hours": resolution["duration_hours"],
        "purpose": resolution["purpose"],
        "business_domain_profiles": resolution["business_domain_profiles"],
        "network_profile": resolution["network_profile"],
        "resolution_status": resolution["resolution_status"],
        "manifest_digest": resolution["manifest_digest"],
        "runtime_authorized": False,
    }
