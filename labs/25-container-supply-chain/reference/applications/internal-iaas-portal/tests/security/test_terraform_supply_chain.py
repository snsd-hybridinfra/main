from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from terraform_runner.executor import module_content_digest
from terraform_runner.supply_chain import (
    PROVIDER_SOURCE,
    SupplyChainError,
    load_supply_chain,
    sanitized_attestation,
    validate_module_source,
    validate_plan_json,
)


ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "terraform/supply-chain-lock.json"
CATALOG = ROOT / "terraform/catalog.json"


def plan(operation: str = "APPLY") -> dict:
    action = "create" if operation == "APPLY" else "delete"
    return {
        "resource_changes": [
            {
                "type": resource_type,
                "provider_name": PROVIDER_SOURCE,
                "change": {"actions": [action]},
            }
            for resource_type in (
                "openstack_networking_port_v2",
                "openstack_compute_instance_v2",
            )
        ]
    }


def test_current_lock_catalog_and_all_modules_are_exact() -> None:
    lock = load_supply_chain(LOCK, CATALOG)
    for module_name, policy in lock["modules"].items():
        result = validate_module_source(
            ROOT / "terraform/modules" / module_name,
            module_name,
            policy,
            module_content_digest,
        )
        assert result["module_digest"] == policy["artifact_digest"]


def test_catalog_tamper_is_denied(tmp_path: Path) -> None:
    target = tmp_path / "catalog.json"
    target.write_text(CATALOG.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SupplyChainError, match="catalog digest"):
        load_supply_chain(LOCK, target)


def test_extra_module_file_is_denied(tmp_path: Path) -> None:
    lock = load_supply_chain(LOCK, CATALOG)
    name = "openstack-dev-vm-small"
    target = tmp_path / name
    shutil.copytree(ROOT / "terraform/modules" / name, target)
    (target / "backdoor.tf").write_text("resource \"null_resource\" \"x\" {}", encoding="utf-8")
    with pytest.raises(SupplyChainError, match="file set"):
        validate_module_source(target, name, lock["modules"][name], module_content_digest)


def test_apply_and_destroy_saved_plans_are_bounded() -> None:
    policy = load_supply_chain(LOCK, CATALOG)["modules"]["openstack-dev-vm-small"]
    assert validate_plan_json(plan("APPLY"), policy, "APPLY")["policy_decision"] == "PASSED"
    assert validate_plan_json(plan("DESTROY"), policy, "DESTROY")["policy_decision"] == "PASSED"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["resource_changes"].append({"type": "null_resource", "provider_name": PROVIDER_SOURCE, "change": {"actions": ["create"]}}), "resource type"),
        (lambda value: value["resource_changes"][0].update({"provider_name": "registry.terraform.io/hashicorp/null"}), "provider substitution"),
        (lambda value: value["resource_changes"][0]["change"].update({"actions": ["update"]}), "unapproved apply action"),
        (lambda value: value["resource_changes"][0]["change"].update({"actions": ["delete", "create"]}), "unapproved apply action"),
    ],
)
def test_extra_provider_update_and_replacement_are_denied(mutation, message: str) -> None:
    policy = load_supply_chain(LOCK, CATALOG)["modules"]["openstack-dev-vm-small"]
    value = plan("APPLY")
    mutation(value)
    with pytest.raises(SupplyChainError, match=message):
        validate_plan_json(value, policy, "APPLY")


def test_attestation_is_sanitized_and_contains_no_runtime_inputs() -> None:
    policy = load_supply_chain(LOCK, CATALOG)["modules"]["openstack-dev-vm-small"]
    attestation = sanitized_attestation(
        module_validation={"module": "openstack-dev-vm-small", "module_digest": policy["artifact_digest"]},
        plan_validation=validate_plan_json(plan(), policy, "APPLY"),
        terraform_version="1.16.1",
        terraform_sha256="sha256:" + "a" * 64,
        provider_sha256="sha256:" + "b" * 64,
    )
    text = json.dumps(attestation).lower()
    assert "clouds.yaml" not in text
    assert "tfvars" not in text
    assert "secret" not in text
    assert "input_values" not in text
