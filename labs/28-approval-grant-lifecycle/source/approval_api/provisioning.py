from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any

from .models import ApprovalRequest


@dataclass(frozen=True, slots=True)
class ProductSpec:
    product_id: str
    product_version: int
    module_name: str
    module_version: str
    artifact_digest: str
    configuration_digest: str | None
    cpu: int
    memory_gib: int
    storage_gib: int
    workload_purposes: frozenset[str]


COMPUTE_PURPOSES = frozenset(
    {"saas-application-development", "backend-integration-test", "security-validation"}
)
KUBERNETES_PURPOSES = frozenset(
    {"saas-deployment-test", "microservice-container-lab", "cicd-integration-test"}
)


def _spec(
    product_id: str,
    module_name: str,
    artifact_digest: str,
    runtime: tuple[int, int, int],
    purposes: frozenset[str] = COMPUTE_PURPOSES,
    configuration_digest: str | None = None,
) -> ProductSpec:
    return ProductSpec(
        product_id,
        1,
        module_name,
        "1.0.0",
        artifact_digest,
        configuration_digest,
        *runtime,
        purposes,
    )


TERRAFORM_PRODUCTS: dict[str, ProductSpec] = {
    "DEV-OS-VM-S": _spec(
        "DEV-OS-VM-S", "openstack-dev-vm-small", "sha256:97f4ece588f80e2ea24524e07d5662c5d6d93b78bcccf75bb935fad99ae090f0", (2, 2, 30)
    ),
    "DEV-OS-VM-M": _spec(
        "DEV-OS-VM-M", "openstack-dev-vm-medium", "sha256:624d5ff0d50bfc97c733a48b78d2d4e4f3cdf4633898a1b5e52ad4003f28a10a", (2, 4, 50)
    ),
    "DEV-OS-VM-L": _spec(
        "DEV-OS-VM-L", "openstack-dev-vm-large", "sha256:b09a0e5e839100bfb09e09469738eca9195418bf2e93153e5f03bcc21db2deae", (2, 8, 80)
    ),
    "DEV-OS-K3S-S": _spec(
        "DEV-OS-K3S-S", "openstack-dev-k3s-small", "sha256:fa1542d73dd9f6c3e7981bd9fe6d0c18564180055f7890ed98aa6575e3286960", (2, 4, 40), KUBERNETES_PURPOSES, "sha256:27ae92895d90f49a118c2fa5db7e897173e15fa002796090765872769c4a6e18"
    ),
    "DEV-OS-K3S-M": _spec(
        "DEV-OS-K3S-M", "openstack-dev-k3s-medium", "sha256:12867fb8f7fef31fe34d63305b13555fb1ef3fd37ea789daa6e67b9a4ba5b03a", (2, 8, 80), KUBERNETES_PURPOSES, "sha256:27ae92895d90f49a118c2fa5db7e897173e15fa002796090765872769c4a6e18"
    ),
}


def module_for_product(product_code: str) -> ProductSpec | None:
    return TERRAFORM_PRODUCTS.get(product_code)


def _manifest_digest(manifest: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    encoded = json.dumps(
        unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_blueprint_manifest(item: Any, spec: ProductSpec, parameters: dict[str, Any]) -> None:
    blueprint_id = getattr(item, "blueprint_id", None) or parameters.get("_blueprint_id")
    manifest_digest = getattr(item, "manifest_digest", None) or parameters.get("_manifest_digest")
    manifest = getattr(item, "resolved_manifest", None) or parameters.get("_resolved_manifest")
    if blueprint_id is None:
        if manifest_digest is not None or manifest is not None:
            raise ValueError("orphan blueprint manifest metadata")
        return
    if blueprint_id != "VM_APPLICATION_STACK" or not isinstance(manifest, dict):
        raise ValueError("blueprint is not in the executable allow-list")
    if manifest_digest != manifest.get("manifest_digest") or manifest_digest != _manifest_digest(manifest):
        raise ValueError("blueprint manifest digest is invalid")
    size_profiles = {
        "SMALL": "DEV-OS-VM-S",
        "STANDARD": "DEV-OS-VM-M",
        "LARGE": "DEV-OS-VM-L",
    }
    if (
        manifest.get("blueprint_id") != blueprint_id
        or manifest.get("environment") not in {"DEV", "TEST", "STG"}
        or size_profiles.get(str(manifest.get("size"))) != spec.product_id
        or manifest.get("duration_hours") != int(item.duration_hours)
        or manifest.get("purpose") != str(item.purpose)
        or manifest.get("network_profile") != "PRIVATE_APPLICATION"
        or manifest.get("selected_execution_profile") != spec.product_id
        or manifest.get("deployment_transaction") != "ALL_OR_NOTHING"
        or manifest.get("resolution_status") != "RESOLVED_LOCAL"
        or manifest.get("blocking_components") != []
        or manifest.get("runtime_authorized") is not False
    ):
        raise ValueError("blueprint manifest does not match the approved request")
    expected_plan = [
        {"component_id": "COMPUTE_VM", "binding_status": "EXECUTION_PROFILE_BOUND_LOCAL"},
        {"component_id": "NETWORK_POLICY", "binding_status": "POLICY_BOUND_LOCAL"},
        {"component_id": "OPERATIONS_PROFILE", "binding_status": "POLICY_BOUND_LOCAL"},
    ]
    if manifest.get("component_plan") != expected_plan or manifest.get(
        "rollback_component_order"
    ) != ["OPERATIONS_PROFILE", "NETWORK_POLICY", "COMPUTE_VM"]:
        raise ValueError("blueprint component or rollback plan is invalid")
    if (
        parameters.get("_blueprint_id") != blueprint_id
        or parameters.get("_blueprint_environment") != manifest.get("environment")
        or parameters.get("_blueprint_size") != manifest.get("size")
        or parameters.get("_manifest_digest") != manifest_digest
    ):
        raise ValueError("blueprint request metadata differs from its manifest")


def validate_product_request(item: Any) -> ProductSpec:
    spec = module_for_product(str(item.product_code))
    if spec is None:
        raise ValueError("product is not in the approved catalog")
    if (int(item.cpu), int(item.memory_gib), int(item.storage_gib)) != (
        spec.cpu,
        spec.memory_gib,
        spec.storage_gib,
    ):
        raise ValueError("request runtime spec does not match the approved product SKU")
    if int(item.duration_hours) not in {4, 8, 24, 72, 168}:
        raise ValueError("request duration is not approved")
    parameters = dict(item.parameters or {})
    project_name = str(parameters.get("project_name", ""))
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,39}", project_name):
        raise ValueError("project_name is invalid")
    if str(parameters.get("workload_purpose", "")) not in spec.workload_purposes:
        raise ValueError("workload_purpose is not approved")
    blueprint_id = getattr(item, "blueprint_id", None) or parameters.get("_blueprint_id")
    allowed_parameters = {"project_name", "workload_purpose"}
    if blueprint_id is not None:
        allowed_parameters.update(
            {
                "_blueprint_id",
                "_blueprint_environment",
                "_blueprint_size",
                "_manifest_digest",
            }
        )
        if "_resolved_manifest" in parameters:
            allowed_parameters.add("_resolved_manifest")
    if set(parameters) != allowed_parameters:
        raise ValueError("request includes unsupported product parameters")
    _validate_blueprint_manifest(item, spec, parameters)
    return spec


def approved_inputs(item: ApprovalRequest, *, approved_by: str) -> dict[str, Any]:
    spec = TERRAFORM_PRODUCTS[item.product_code]
    expires_at = datetime.now(timezone.utc) + timedelta(hours=item.duration_hours)
    project_name = str((item.parameters or {}).get("project_name", ""))
    values = {
        "request_id": item.request_id,
        "owner_id": item.requester_id,
        "project_name": project_name,
        "workload_purpose": str((item.parameters or {}).get("workload_purpose", "")),
        "product_id": spec.product_id,
        "product_version": spec.product_version,
        "module_version": spec.module_version,
        "artifact_digest": spec.artifact_digest,
        "expires_at": expires_at.isoformat(),
        "approved_by": approved_by,
        "required_tags": {
            "RequestId": item.request_id,
            "OwnerId": item.requester_id,
            "ProductId": spec.product_id,
            "ExpiresAt": expires_at.isoformat(),
            "ManagedBy": "terraform-runner",
            "Exposure": "private-only",
        },
    }
    if spec.configuration_digest:
        values["configuration_digest"] = spec.configuration_digest
    manifest = (item.parameters or {}).get("_resolved_manifest")
    if isinstance(manifest, dict):
        values.update(
            {
                "blueprint_id": manifest["blueprint_id"],
                "manifest_digest": manifest["manifest_digest"],
                "resolved_manifest": manifest,
            }
        )
        values["required_tags"].update(
            {
                "BlueprintId": manifest["blueprint_id"],
                "ManifestDigest": manifest["manifest_digest"],
            }
        )
    return values


def logical_resource_id(request_id: str) -> str:
    return f"WRK-{request_id.replace('-', '')[:32]}"
