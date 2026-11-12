from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from terraform_runner.config import Settings
from terraform_runner.executor import (
    ALLOWED_MODULES,
    Executor,
    TerraformExecutionError,
    module_content_digest,
)


MODULE_PRODUCTS = {
    "openstack-dev-vm-small": (
        "DEV-OS-VM-S",
        "sha256:97f4ece588f80e2ea24524e07d5662c5d6d93b78bcccf75bb935fad99ae090f0",
    ),
    "openstack-dev-vm-medium": (
        "DEV-OS-VM-M",
        "sha256:624d5ff0d50bfc97c733a48b78d2d4e4f3cdf4633898a1b5e52ad4003f28a10a",
    ),
    "openstack-dev-vm-large": (
        "DEV-OS-VM-L",
        "sha256:b09a0e5e839100bfb09e09469738eca9195418bf2e93153e5f03bcc21db2deae",
    ),
    "openstack-dev-k3s-small": (
        "DEV-OS-K3S-S",
        "sha256:fa1542d73dd9f6c3e7981bd9fe6d0c18564180055f7890ed98aa6575e3286960",
    ),
    "openstack-dev-k3s-medium": (
        "DEV-OS-K3S-M",
        "sha256:12867fb8f7fef31fe34d63305b13555fb1ef3fd37ea789daa6e67b9a4ba5b03a",
    ),
}


def job(operation: str = "APPLY", module: str = "openstack-dev-vm-small") -> dict:
    product_code, digest = MODULE_PRODUCTS.get(
        module, ("DEV-OS-VM-S", MODULE_PRODUCTS["openstack-dev-vm-small"][1])
    )
    item = {
        "job_id": "job-1",
        "request_id": "request-1",
        "operation": operation,
        "product_code": product_code,
        "product_version": 1,
        "module_name": module,
        "module_version": "1.0.0",
        "artifact_digest": digest,
        "resource_id": "WRK-request1",
        "state_key": "requests/request-1/terraform.tfstate",
        "input_values": {
            "request_id": "request-1",
            "owner_id": "user-1",
            "project_name": "payment-api-test",
            "workload_purpose": "saas-application-development",
            "product_id": product_code,
            "product_version": 1,
            "expires_at": "2026-08-13T23:59:59+09:00",
            "approved_by": "approver-1",
            "required_tags": {
                "RequestId": "request-1",
                "OwnerId": "user-1",
                "ProductId": product_code,
                "ExpiresAt": "2026-08-13T23:59:59+09:00",
                "ManagedBy": "terraform-runner",
                "Exposure": "private-only",
            },
        },
    }
    if "k3s" in module:
        item["input_values"]["configuration_digest"] = (
            "sha256:27ae92895d90f49a118c2fa5db7e897173e15fa002796090765872769c4a6e18"
        )
    return item


def test_mock_runner_uses_same_progress_and_validated_result_contract() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(job(), reports.append)
    assert [item["status"] for item in reports] == ["PROVISIONING", "RUNNING"]
    assert reports[-1]["validation_passed"] is True
    assert reports[-1]["endpoint"].startswith("10.")
    assert reports[-1]["details"]["module"] == "openstack-dev-vm-small"
    assert reports[-1]["details"]["network_exposure"] == "PRIVATE_ONLY"
    assert reports[-1]["details"]["floating_ip"] is False


def test_mock_destroy_reports_termination() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(
        job(operation="DESTROY"), reports.append
    )
    assert [item["status"] for item in reports] == ["TERMINATING", "TERMINATED"]


def test_mock_runner_supports_all_openstack_compute_skus() -> None:
    for module in MODULE_PRODUCTS:
        reports: list[dict] = []
        Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(
            job(module=module), reports.append
        )
        assert [item["status"] for item in reports] == ["PROVISIONING", "RUNNING"]
        assert reports[-1]["endpoint"].startswith(("10.", "https://10."))
        assert reports[-1]["validation_passed"] is True


def test_mock_k3s_reports_validated_bootstrap_without_exposing_credentials() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(
        job(module="openstack-dev-k3s-small"), reports.append
    )
    assert reports[-1]["details"]["bootstrap_status"] == "READY"
    assert reports[-1]["endpoint"].startswith("https://10.")
    assert "token" not in str(reports[-1]).lower()
    assert "kubeconfig" not in str(reports[-1]).lower()


def test_runner_rejects_arbitrary_module() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(
        job(module="../../malicious"), reports.append
    )
    assert [item["status"] for item in reports] == ["PROVISION_FAILED"]
    assert reports[0]["failure_code"] == "POLICY_DENIED"


def test_terraform_mode_is_fail_closed_without_runtime_authorization() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="terraform", deployment_authorized=False)).run(
        job(), reports.append
    )
    assert [item["status"] for item in reports] == ["PROVISION_FAILED"]
    assert reports[0]["failure_code"] == "POLICY_DENIED"
    assert "explicit runtime authorization" in reports[0]["error"]


def test_real_k3s_apply_requires_separate_configuration_authorization() -> None:
    reports: list[dict] = []
    Executor(Settings(runner_mode="terraform", deployment_authorized=True)).run(
        job(module="openstack-dev-k3s-small"), reports.append
    )
    assert [item["status"] for item in reports] == ["PROVISION_FAILED"]
    assert reports[0]["failure_code"] == "BOOTSTRAP_VALIDATION_REQUIRED"
    assert "separate runtime authorization" in reports[0]["error"]


def test_approved_module_digest_matches_repository_content() -> None:
    root = Path(__file__).resolve().parents[2]
    assert set(ALLOWED_MODULES) == set(MODULE_PRODUCTS)
    for module, (_, digest) in MODULE_PRODUCTS.items():
        assert module_content_digest(root / "terraform/modules" / module) == digest


def _real_k3s_settings(tmp_path: Path) -> Settings:
    root = Path(__file__).resolve().parents[2]
    clouds = tmp_path / "clouds.yaml"
    private_key = tmp_path / "runner-key"
    known_hosts = tmp_path / "known_hosts"
    binary = tmp_path / "k3s"
    images = tmp_path / "k3s-airgap-images-amd64.tar.zst"
    terraform_binary = tmp_path / "terraform"
    provider_mirror = tmp_path / "provider-mirror"
    provider_package = provider_mirror / "terraform-provider-openstack_v3.4.0"
    clouds.write_text("clouds: {}", encoding="utf-8")
    private_key.write_text("external-test-key-path", encoding="utf-8")
    known_hosts.write_text("10.250.2.20 ssh-ed25519 test-key", encoding="utf-8")
    binary.write_bytes(b"pinned-k3s-binary")
    images.write_bytes(b"pinned-k3s-airgap-images")
    terraform_binary.write_bytes(b"pinned-terraform-cli")
    provider_mirror.mkdir()
    provider_package.write_bytes(b"pinned-openstack-provider")
    return Settings(
        runner_mode="terraform",
        terraform_bin=str(terraform_binary),
        terraform_binary_sha256=hashlib.sha256(terraform_binary.read_bytes()).hexdigest(),
        terraform_supply_chain_lock=str(root / "terraform/supply-chain-lock.json"),
        terraform_catalog=str(root / "terraform/catalog.json"),
        terraform_provider_mirror_root=str(provider_mirror),
        openstack_provider_package=str(provider_package),
        openstack_provider_package_sha256=hashlib.sha256(provider_package.read_bytes()).hexdigest(),
        deployment_authorized=True,
        k3s_configuration_authorized=True,
        module_root=str(root / "terraform/modules"),
        work_root=str(tmp_path / "work"),
        state_root=str(tmp_path / "state"),
        clouds_config_file=str(clouds),
        cloud_name="approved-cloud",
        target_region="RegionOne",
        network_id="network-1",
        security_group_ids=("sg-1",),
        approved_k3s_image_name="approved-base-image",
        keypair_name="approved-keypair",
        flavor_medium="approved-medium",
        ansible_root=str(root / "ansible"),
        ansible_remote_user="automation-user",
        ansible_private_key_file=str(private_key),
        ansible_known_hosts_file=str(known_hosts),
        k3s_binary_path=str(binary),
        k3s_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        k3s_airgap_images_path=str(images),
        k3s_airgap_images_sha256=hashlib.sha256(images.read_bytes()).hexdigest(),
    )


def _terraform_output() -> str:
    values = {
        "primary_resource_id": "instance-1",
        "endpoint": "https://10.250.2.20:6443",
        "display_name": "test / OpenStack k3s PaaS Small",
        "floating_ip": False,
        "network_exposure": "PRIVATE_ONLY",
        "bootstrap_status": "CONFIGURATION_REQUIRED",
        "monitoring_status": "NOT_ONBOARDED",
    }
    return json.dumps({key: {"value": value} for key, value in values.items()})


def _terraform_state(item: dict) -> str:
    return json.dumps(
        {
            "values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "openstack_compute_instance_v2",
                            "values": {
                                "power_state": "active",
                                "image_name": "approved-base-image",
                                "flavor_name": "approved-medium",
                                "key_pair": "approved-keypair",
                                "metadata": item["input_values"]["required_tags"],
                            },
                        },
                        {
                            "type": "openstack_networking_port_v2",
                            "values": {
                                "network_id": "network-1",
                                "port_security_enabled": True,
                                "security_group_ids": ["sg-1"],
                            },
                        },
                    ]
                }
            }
        }
    )


def _terraform_plan(operation: str = "APPLY") -> str:
    action = "create" if operation == "APPLY" else "delete"
    return json.dumps(
        {
            "resource_changes": [
                {
                    "type": resource_type,
                    "provider_name": "registry.terraform.io/terraform-provider-openstack/openstack",
                    "change": {"actions": [action]},
                }
                for resource_type in (
                    "openstack_networking_port_v2",
                    "openstack_compute_instance_v2",
                )
            ]
        }
    )


def test_approved_k3s_runs_terraform_then_ansible(monkeypatch, tmp_path: Path) -> None:
    item = job(module="openstack-dev-k3s-small")
    commands: list[list[str]] = []

    def fake_command(command, cwd, environment, *, failure_code):
        commands.append(command)
        if command[0] == "ansible-playbook":
            return "PLAY RECAP approved-k3s-target ok=20 changed=8 failed=0"
        if command[1:] == ["version", "-json"]:
            return json.dumps({"terraform_version": "1.16.1"})
        if "output" in command:
            return _terraform_output()
        if "show" in command and "tfplan" in command:
            return _terraform_plan("DESTROY" if "-destroy" in " ".join(" ".join(item) for item in commands) else "APPLY")
        if "show" in command:
            return _terraform_state(item)
        return ""

    monkeypatch.setattr(Executor, "_command", staticmethod(fake_command))
    reports: list[dict] = []
    Executor(_real_k3s_settings(tmp_path)).run(item, reports.append)
    assert [value["status"] for value in reports] == ["PROVISIONING", "RUNNING"]
    assert reports[-1]["details"]["bootstrap_status"] == "READY"
    assert reports[-1]["outputs"]["configuration_provisioner"] == "ANSIBLE"
    apply_index = next(index for index, value in enumerate(commands) if "apply" in value)
    ansible_index = next(
        index for index, value in enumerate(commands) if value[0] == "ansible-playbook"
    )
    assert apply_index < ansible_index
    assert not any("-destroy" in value for value in commands)
    assert reports[-1]["outputs"]["supply_chain_attestation"]["decision"] == "PASSED"


@pytest.mark.parametrize("residual_resource", [False, True])
def test_ansible_failure_triggers_automatic_terraform_destroy(
    monkeypatch, tmp_path: Path, residual_resource: bool
) -> None:
    item = job(module="openstack-dev-k3s-small")
    commands: list[list[str]] = []

    def fake_command(command, cwd, environment, *, failure_code):
        commands.append(command)
        if command[0] == "ansible-playbook":
            raise TerraformExecutionError("bounded configuration failure", failure_code)
        if command[1:] == ["version", "-json"]:
            return json.dumps({"terraform_version": "1.16.1"})
        if "output" in command:
            return _terraform_output()
        if "show" in command and "tfplan" in command:
            operation = "DESTROY" if any("-destroy" in value for value in commands) else "APPLY"
            return _terraform_plan(operation)
        if "show" in command:
            if any("-destroy" in value for value in commands):
                return (
                    _terraform_state(item) if residual_resource
                    else json.dumps({"format_version": "1.0"})
                )
            return _terraform_state(item)
        return ""

    monkeypatch.setattr(Executor, "_command", staticmethod(fake_command))
    reports: list[dict] = []
    Executor(_real_k3s_settings(tmp_path)).run(item, reports.append)
    assert [value["status"] for value in reports] == ["PROVISIONING", "PROVISION_FAILED"]
    assert reports[-1]["failure_code"] == (
        "ROLLBACK_FAILED" if residual_resource else "CONFIGURATION_FAILED"
    )
    assert reports[-1]["validation_passed"] is False
    assert reports[-1]["details"]["recovery_status"] == (
        "ROLLBACK_FAILED" if residual_resource else "ROLLED_BACK"
    )
    assert reports[-1]["details"]["recovery_verification"] == (
        "NOT_PROVEN" if residual_resource else "TERRAFORM_STATE_EMPTY"
    )
    ansible_index = next(
        index for index, value in enumerate(commands) if value[0] == "ansible-playbook"
    )
    destroy_index = next(index for index, value in enumerate(commands) if "-destroy" in value)
    assert ansible_index < destroy_index


@pytest.mark.parametrize("rollback_succeeds", [True, False])
def test_post_apply_policy_failure_triggers_verified_automatic_rollback(
    monkeypatch, tmp_path: Path, rollback_succeeds: bool
) -> None:
    item = job()
    commands: list[list[str]] = []

    def fake_command(command, cwd, environment, *, failure_code):
        commands.append(command)
        destroy_started = any("-destroy" in value for value in commands)
        if command[1:] == ["version", "-json"]:
            return json.dumps({"terraform_version": "1.16.1"})
        if "output" in command:
            return _terraform_output()
        if "show" in command and "tfplan" in command:
            return _terraform_plan("DESTROY" if destroy_started else "APPLY")
        if command[1:] == ["show", "-json"] and destroy_started:
            return (
                json.dumps({"format_version": "1.0"})
                if rollback_succeeds
                else _terraform_state(item)
            )
        if command[1:] == ["show", "-json"]:
            state = json.loads(_terraform_state(item))
            resources = state["values"]["root_module"]["resources"]
            instance = next(
                value for value in resources if value["type"] == "openstack_compute_instance_v2"
            )
            instance["values"]["metadata"]["OwnerId"] = "unapproved-owner"
            return json.dumps(state)
        return ""

    monkeypatch.setattr(Executor, "_command", staticmethod(fake_command))
    settings = replace(
        _real_k3s_settings(tmp_path),
        approved_image_name="approved-base-image",
        flavor_small="approved-medium",
    )
    reports: list[dict] = []
    Executor(settings).run(item, reports.append)

    assert [value["status"] for value in reports] == ["PROVISIONING", "PROVISION_FAILED"]
    assert reports[-1]["failure_code"] == (
        "POLICY_DENIED" if rollback_succeeds else "ROLLBACK_FAILED"
    )
    assert reports[-1]["details"]["recovery_status"] == (
        "ROLLED_BACK" if rollback_succeeds else "ROLLBACK_FAILED"
    )
    assert reports[-1]["details"]["recovery_verification"] == (
        "TERRAFORM_STATE_EMPTY" if rollback_succeeds else "NOT_PROVEN"
    )
    apply_index = next(index for index, value in enumerate(commands) if "apply" in value)
    destroy_index = next(index for index, value in enumerate(commands) if "-destroy" in value)
    assert apply_index < destroy_index


@pytest.mark.parametrize(
    ("post_destroy_state", "succeeds"),
    [
        ('{"format_version":"1.0"}', True),
        ('{"format_version":"1.0","values":{"root_module":{}}}', True),
        ('{"format_version":"1.0","values":{"root_module":{"resources":[],"child_modules":[{"resources":[]}]}}}', True),
        ('{"format_version":"1.0","values":{"root_module":{"resources":[{"type":"openstack_compute_instance_v2"}]}}}', False),
        ('{"format_version":"1.0","values":{"root_module":{"child_modules":[{"child_modules":[{"resources":[{"type":"openstack_networking_port_v2"}]}]}]}}}', False),
        ('{"format_version":"1.0","values":null}', False),
        ('{"format_version":"1.0","values":{"root_module":{"resources":null}}}', False),
        ('{"format_version":"1.0","values":{"root_module":{"child_modules":{}}}}', False),
        ('{"format_version":"1.0","values":{"root_module":{"child_modules":[null]}}}', False),
        ('{"format_version":"2.0"}', False),
        ('{}', False),
        ('[]', False),
        ('not-json-sensitive-runtime-value', False),
        (None, False),
    ],
    ids=[
        "empty-state", "empty-root", "empty-child", "residual-vm",
        "nested-residual-port", "null-values", "null-resources",
        "invalid-children", "null-child", "unsupported-format",
        "missing-format", "invalid-top-level", "invalid-json", "read-failure",
    ],
)
def test_real_destroy_requires_verified_empty_state(
    monkeypatch, tmp_path: Path, post_destroy_state: str | None, succeeds: bool
) -> None:
    commands: list[list[str]] = []

    def fake_command(command, cwd, environment, *, failure_code):
        commands.append(command)
        if command[1:] == ["version", "-json"]:
            return json.dumps({"terraform_version": "1.16.1"})
        if "show" in command and "tfplan" in command:
            return _terraform_plan("DESTROY")
        if command[1:] == ["show", "-json"]:
            if post_destroy_state is None:
                raise TerraformExecutionError("sensitive-runtime-value", failure_code)
            return post_destroy_state
        return ""

    monkeypatch.setattr(Executor, "_command", staticmethod(fake_command))
    settings = replace(
        _real_k3s_settings(tmp_path),
        approved_image_name="approved-base-image",
        flavor_small="approved-small",
    )
    state_file = Path(settings.state_root) / job()["state_key"]
    state_file.parent.mkdir(parents=True)
    state_file.write_bytes(b"synthetic-external-state-for-reviewed-recovery")
    reports: list[dict] = []
    Executor(settings).run(job(operation="DESTROY"), reports.append)
    assert [value["status"] for value in reports] == [
        "TERMINATING", "TERMINATED" if succeeds else "TERMINATION_FAILED"
    ]
    assert reports[-1]["validation_passed"] is succeeds
    if succeeds:
        assert reports[-1]["outputs"]["destroyed"] is True
    else:
        assert reports[-1]["failure_code"] == "DESTROY_FAILED"
        assert reports[-1]["outputs"] == {}
    assert "sensitive-runtime-value" not in json.dumps(reports)
    assert not (Path(settings.work_root) / "job-1").exists()
    assert state_file.read_bytes() == b"synthetic-external-state-for-reviewed-recovery"
    destroy_apply = next(index for index, value in enumerate(commands) if "apply" in value)
    state_read = next(index for index, value in enumerate(commands) if value[1:] == ["show", "-json"])
    assert destroy_apply < state_read


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(operation="IMPORT"),
        lambda value: value.update(job_id="../job-1"),
        lambda value: value.pop("job_id"),
        lambda value: value.update(state_key="requests/request-2/terraform.tfstate"),
        lambda value: value.update(state_key="../terraform.tfstate"),
        lambda value: value["input_values"].update(request_id="request-2"),
        lambda value: value["input_values"].update(product_id="DEV-OS-VM-L"),
        lambda value: value["input_values"].update(product_version=2),
        lambda value: value["input_values"]["required_tags"].update(OwnerId="user-2"),
        lambda value: value["input_values"]["required_tags"].update(ProductId="DEV-OS-VM-L"),
        lambda value: value["input_values"]["required_tags"].update(ExpiresAt="different-expiry"),
        lambda value: value.update(input_values=[]),
        lambda value: value["input_values"].update(required_tags=[]),
    ],
    ids=[
        "operation", "job-path", "missing-job", "other-request-state",
        "state-traversal", "request-binding", "product-binding", "version-binding",
        "owner-tag", "product-tag", "expiry-tag", "input-type", "tag-type",
    ],
)
def test_job_boundary_tampering_is_denied_before_execution(monkeypatch, mutation) -> None:
    item = job()
    mutation(item)
    executions: list[dict] = []
    monkeypatch.setattr(Executor, "_run_mock", lambda _, value: executions.append(value))
    reports: list[dict] = []
    Executor(Settings(runner_mode="mock", mock_delay_seconds=0)).run(item, reports.append)
    assert not executions
    assert len(reports) == 1
    assert reports[0]["failure_code"] == "POLICY_DENIED"
    assert reports[0]["validation_passed"] is False


def test_unauthorized_run_preserves_existing_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "work" / "job-1"
    workspace.mkdir(parents=True)
    marker = workspace / "preserve.txt"
    marker.write_bytes(b"existing-workspace-not-owned-by-this-run")
    reports: list[dict] = []
    Executor(Settings(runner_mode="terraform", work_root=str(workspace.parent))).run(
        job(), reports.append
    )
    assert reports[0]["failure_code"] == "POLICY_DENIED"
    assert marker.read_bytes() == b"existing-workspace-not-owned-by-this-run"


@pytest.mark.parametrize(
    "case",
    [
        "git-state", "git-work", "git-credentials", "state-in-work",
        "work-in-state", "shared-root", "credentials-in-work",
        "relative-state", "relative-work", "existing-workspace",
        "git-key", "key-in-work",
    ],
)
def test_unsafe_runtime_paths_are_denied_without_commands_or_deletion(
    monkeypatch, tmp_path: Path, case: str
) -> None:
    settings = replace(
        _real_k3s_settings(tmp_path),
        approved_image_name="approved-base-image",
        flavor_small="approved-small",
    )
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()
    (fake_repo / ".git").write_text("gitdir: external-test-only", encoding="utf-8")
    work = Path(settings.work_root)
    state = Path(settings.state_root)
    clouds = Path(settings.clouds_config_file)
    if case == "git-state":
        state = fake_repo / "state"
    elif case == "git-work":
        work = fake_repo / "work"
    elif case == "git-credentials":
        clouds = fake_repo / "clouds.yaml"
    elif case == "state-in-work":
        state = work / "protected-state"
    elif case == "work-in-state":
        work = state / "work"
    elif case == "shared-root":
        state = work
    elif case == "credentials-in-work":
        clouds = work / "clouds.yaml"
    elif case in {"git-key", "key-in-work"}:
        key = (fake_repo if case == "git-key" else work) / "runner-key"
        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_bytes(b"synthetic-key-preserve")
        settings = replace(settings, ansible_private_key_file=str(key))
    clouds.parent.mkdir(parents=True, exist_ok=True)
    clouds.write_bytes(b"synthetic-credential-reference-preserve")
    state_file = state / job()["state_key"]
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_bytes(b"synthetic-state-preserve")
    marker = work / "job-1" / "preserve.txt"
    if case == "existing-workspace":
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b"existing-workspace-preserve")
    settings = replace(
        settings,
        state_root="relative-state" if case == "relative-state" else str(state),
        work_root="relative-work" if case == "relative-work" else str(work),
        clouds_config_file=str(clouds),
    )
    commands: list[list[str]] = []
    monkeypatch.setattr(
        Executor, "_command", staticmethod(lambda command, *args, **kwargs: commands.append(command))
    )
    reports: list[dict] = []
    Executor(settings).run(job(), reports.append)
    assert not commands
    assert len(reports) == 1
    assert reports[0]["failure_code"] == "POLICY_DENIED"
    assert state_file.read_bytes() == b"synthetic-state-preserve"
    assert clouds.read_bytes() == b"synthetic-credential-reference-preserve"
    if case == "existing-workspace":
        assert marker.read_bytes() == b"existing-workspace-preserve"
    if case in {"git-key", "key-in-work"}:
        assert Path(settings.ansible_private_key_file).read_bytes() == b"synthetic-key-preserve"
    assert "synthetic-credential" not in json.dumps(reports)
