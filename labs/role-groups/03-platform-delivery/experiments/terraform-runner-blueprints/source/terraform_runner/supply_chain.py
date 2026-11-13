"""Independent Terraform artifact and saved-plan supply-chain authority."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable


PROVIDER_SOURCE = "registry.terraform.io/terraform-provider-openstack/openstack"
MODULE_FILES = {"main.tf", "outputs.tf", "variables.tf", "versions.tf"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SupplyChainError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SupplyChainError(f"cannot read supply-chain authority: {path}") from exc
    if not isinstance(value, dict):
        raise SupplyChainError(f"supply-chain authority is not an object: {path}")
    return value


def load_supply_chain(lock_path: Path, catalog_path: Path) -> dict[str, Any]:
    lock = _json(lock_path)
    catalog = _json(catalog_path)
    if lock.get("schema_version") != "1.0.0" or lock.get("status") != "LOCAL_CANDIDATE":
        raise SupplyChainError("unsupported Terraform supply-chain lock")
    if lock.get("runtime_authorized") is not False:
        raise SupplyChainError("machine lock must not grant runtime authorization")
    engine = lock.get("engine", {})
    if (
        engine.get("distribution") != "HASHICORP_TERRAFORM_CLI"
        or engine.get("version") != "1.16.1"
        or engine.get("core_forked") is not False
        or engine.get("customization") != "SNSD_POLICY_WRAPPER"
    ):
        raise SupplyChainError("Terraform engine identity changed")
    provider = lock.get("provider", {})
    if (
        provider.get("source") != PROVIDER_SOURCE
        or provider.get("version_constraint") != "~> 3.4.0"
        or provider.get("installation") != "FILESYSTEM_MIRROR_ONLY"
        or provider.get("direct_registry_egress") is not False
    ):
        raise SupplyChainError("OpenStack provider authority changed")
    expected_catalog = str(lock.get("catalog", {}).get("sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", expected_catalog) or sha256_file(catalog_path) != f"sha256:{expected_catalog}":
        raise SupplyChainError("Terraform catalog digest mismatch")

    modules = lock.get("modules")
    products = catalog.get("products")
    if not isinstance(modules, dict) or not isinstance(products, dict):
        raise SupplyChainError("module or catalog product authority is missing")
    by_module = {value.get("module_name"): (key, value) for key, value in products.items()}
    if set(modules) != set(by_module):
        raise SupplyChainError("locked module set differs from the catalog")
    for module_name, policy in modules.items():
        product_id, product = by_module[module_name]
        if (
            policy.get("product_id") != product_id
            or policy.get("module_version") != product.get("module_version")
            or policy.get("artifact_digest") != product.get("artifact_digest")
            or policy.get("configuration_digest") != product.get("configuration_digest")
            or policy.get("allowed_resource_types") != product.get("allowed_resource_types")
        ):
            raise SupplyChainError(f"catalog/lock identity mismatch: {module_name}")
        expected_counts = {
            "openstack_networking_port_v2": product.get("max_ports"),
            "openstack_compute_instance_v2": product.get("max_instances"),
        }
        if policy.get("max_resources") != expected_counts:
            raise SupplyChainError(f"catalog/lock resource limit mismatch: {module_name}")
    plan = lock.get("plan_policy", {})
    if (
        plan.get("apply_actions") != [["create"], ["no-op"]]
        or plan.get("destroy_actions") != [["delete"], ["no-op"]]
        or plan.get("replacement_allowed") is not False
        or plan.get("update_allowed") is not False
        or plan.get("saved_plan_apply_only") is not True
    ):
        raise SupplyChainError("saved-plan action policy changed")
    return lock


def validate_module_source(
    module_directory: Path,
    module_name: str,
    policy: dict[str, Any],
    content_digest: Callable[[Path], str],
) -> dict[str, Any]:
    if not module_directory.is_dir() or module_directory.is_symlink():
        raise SupplyChainError("approved module directory is invalid")
    paths = list(module_directory.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise SupplyChainError("Terraform module symlinks are denied")
    files = {path.relative_to(module_directory).as_posix() for path in paths if path.is_file()}
    if files != MODULE_FILES:
        raise SupplyChainError("Terraform module file set is not exact")
    actual_digest = content_digest(module_directory)
    if actual_digest != policy.get("artifact_digest"):
        raise SupplyChainError("Terraform module content digest mismatch")
    versions = (module_directory / "versions.tf").read_text(encoding="utf-8")
    required_tokens = (
        'required_version = ">= 1.7.0, < 2.0.0"',
        'source  = "terraform-provider-openstack/openstack"',
        'version = "~> 3.4.0"',
        'backend "local"',
    )
    if any(token not in versions for token in required_tokens):
        raise SupplyChainError("Terraform module engine/provider constraint changed")
    all_text = "\n".join((module_directory / name).read_text(encoding="utf-8") for name in sorted(files))
    if re.search(r"\bsource\s*=\s*\"(?:git::|https?://|s3::|gcs::)", all_text, re.I):
        raise SupplyChainError("remote Terraform module source is denied")
    return {"module": module_name, "module_digest": actual_digest, "files": sorted(files)}


def validate_plan_json(
    plan: dict[str, Any], policy: dict[str, Any], operation: str
) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(plan.get("resource_changes"), list):
        raise SupplyChainError("saved Terraform plan JSON is malformed")
    if operation not in {"APPLY", "DESTROY"}:
        raise SupplyChainError("unsupported Terraform plan operation")
    allowed_actions = {("create",), ("no-op",)} if operation == "APPLY" else {("delete",), ("no-op",)}
    allowed_types = set(policy.get("allowed_resource_types") or [])
    maximum = policy.get("max_resources") or {}
    counts = {resource_type: 0 for resource_type in allowed_types}
    action_counts: dict[str, int] = {}
    for change in plan["resource_changes"]:
        if not isinstance(change, dict):
            raise SupplyChainError("saved plan contains an invalid resource change")
        resource_type = str(change.get("type", ""))
        if resource_type not in allowed_types:
            raise SupplyChainError(f"saved plan contains an unapproved resource type: {resource_type}")
        if change.get("provider_name") != PROVIDER_SOURCE:
            raise SupplyChainError("saved plan contains provider substitution")
        actions = tuple((change.get("change") or {}).get("actions") or [])
        if actions not in allowed_actions:
            raise SupplyChainError(f"saved plan contains an unapproved {operation.lower()} action: {actions}")
        counts[resource_type] += 1
        action_key = "+".join(actions)
        action_counts[action_key] = action_counts.get(action_key, 0) + 1
    if counts != maximum:
        raise SupplyChainError(f"saved plan resource counts differ from the execution profile: {counts}")
    return {
        "operation": operation,
        "provider": PROVIDER_SOURCE,
        "resource_counts": counts,
        "action_counts": action_counts,
        "policy_decision": "PASSED",
    }


def sanitized_attestation(
    *,
    module_validation: dict[str, Any],
    plan_validation: dict[str, Any],
    terraform_version: str,
    terraform_sha256: str,
    provider_sha256: str,
) -> dict[str, Any]:
    for value in (terraform_sha256, provider_sha256, module_validation.get("module_digest")):
        if not DIGEST_RE.fullmatch(str(value or "")):
            raise SupplyChainError("attestation digest is invalid")
    return {
        "schema_version": "1.0.0",
        "decision": "PASSED",
        "terraform": {"version": terraform_version, "sha256": terraform_sha256},
        "provider": {"source": PROVIDER_SOURCE, "package_sha256": provider_sha256},
        "module": {
            "name": module_validation["module"],
            "sha256": module_validation["module_digest"],
        },
        "plan": plan_validation,
    }
