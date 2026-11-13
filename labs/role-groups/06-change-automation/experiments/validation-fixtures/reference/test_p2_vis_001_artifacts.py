"""Regression tests for P2-VIS-001 bounded runtime and partial promotion."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_p2_vis_001_artifacts as artifacts  # noqa: E402


class P2VisibilityArtifactTests(unittest.TestCase):
    def copied_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in artifacts.REQUIRED_PATHS:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return temporary, root

    def test_current_artifacts_pass(self) -> None:
        self.assertEqual([], artifacts.validate(ROOT))

    def test_floating_ip_resource_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TF_MODULE / "main.tf"
            path.write_text(path.read_text(encoding="utf-8") + '\nresource "openstack_networking_floatingip_v2" "bad" {}\n', encoding="utf-8")
            self.assertTrue(any("Terraform" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_public_host_port_is_rejected(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "templates/compose.yaml.j2"
            value = path.read_text(encoding="utf-8").replace("127.0.0.1:3000:3000", "0.0.0.0:3000:3000")
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("loopback" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_provider_lock_cannot_drop_checksums(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TF_ENV / ".terraform.lock.hcl"
            value = path.read_text(encoding="utf-8").replace('version     = "3.4.0"', 'version     = "3.4.1"')
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("provider lock" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_native_validation_cannot_claim_terraform_apply(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.NATIVE_VALIDATION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["terraform"]["apply"] = "PASS"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("native validation" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_deployment_default_cannot_be_enabled(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "defaults/main.yml"
            value = path.read_text(encoding="utf-8").replace("zt_vis_002_deployment_authorized: false", "zt_vis_002_deployment_authorized: true")
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("fail-closed" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_reviewed_image_manifest_cannot_be_substituted(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "defaults/main.yml"
            value = path.read_text(encoding="utf-8").replace(
                "6ea068891652aa6a65ca9065c26b89de939653803c836426970305c11fd00534",
                "0" * 64,
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("reviewed grafana" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_allow_mutable_image_fallback(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.READINESS
            value = json.loads(path.read_text(encoding="utf-8"))
            value["artifact_policy"]["mutable_fallback_allowed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("artifact policy" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_relabel_reviewed_image_tag(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.READINESS
            value = json.loads(path.read_text(encoding="utf-8"))
            value["artifact_policy"]["images"][0]["tag_reference"] = "docker.io/grafana/grafana:latest"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("source tags" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_merge_recovery_and_dashboard_admin(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.READINESS
            value = json.loads(path.read_text(encoding="utf-8"))
            next(item for item in value["access_policy"]["roles"] if item["role"] == "VISIBILITY_ADMINISTRATOR")["host_recovery_allowed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("access policy" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_readiness_cannot_claim_restore_acceptance(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.READINESS
            value = json.loads(path.read_text(encoding="utf-8"))
            value["retention_restore_policy"]["restore_runtime_accepted"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("retention" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_deploy_playbook_cannot_drop_repository_relative_role(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / "ansible/playbooks/zt-vis-002-deploy.yml"
            value = path.read_text(encoding="utf-8").replace("../roles/zt_vis_002", "zt_vis_002")
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("role path" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_native_validation_cannot_claim_playbook_execution(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.NATIVE_VALIDATION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["ansible"]["playbook_execution"] = "PASS"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("playbook execution" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_vmware_control_node_cannot_enable_bridged_networking(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CONTROL_NODE_PROVISIONER
            value = path.read_text(encoding="utf-8").replace(
                'ethernet0.connectionType = "nat"',
                'ethernet0.connectionType = "bridged"',
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("control-node provisioner" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_native_validation_cannot_restore_wsl_control_authority(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.NATIVE_VALIDATION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["ansible"]["target_control_node"] = "UBUNTU_24_04_WSL1"
            value["ansible"]["wsl_control_node_used"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("VMware Ansible control-node" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_sanitized_control_node_evidence_rejects_dhcp_address(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CONTROL_NODE_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["control_node"]["dhcp_address"] = "192.0.2.10"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("DHCP or MAC" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_package_cannot_drop_artifact_authority(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.PACKAGE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["source_authorities"].remove("tools/validate_p2_vis_001_artifacts.py")
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("package must reference" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_gate_discovery_rejects_resource_address(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_GATE_DISCOVERY
            value = json.loads(path.read_text(encoding="utf-8"))
            value["findings"]["resource_candidates"]["address"] = "192.0.2.10"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("addresses" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_gate_discovery_cannot_hide_cinder_blocker(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_GATE_DISCOVERY
            value = json.loads(path.read_text(encoding="utf-8"))
            value["findings"]["service_catalog"]["block_storage"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("Cinder" in item or "schema" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_gate_discovery_cannot_claim_plan(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_GATE_DISCOVERY
            value = json.loads(path.read_text(encoding="utf-8"))
            value["terraform_plan_created"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("plan" in item or "schema" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_cinder_evidence_rejects_resource_address(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CINDER_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["change_scope"]["address"] = "192.0.2.10"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("Cinder prerequisite evidence" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_cinder_evidence_cannot_promote_visibility_runtime(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CINDER_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["package_boundary"]["package_runtime_executed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("visibility runtime" in item or "schema" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_cinder_evidence_cannot_drop_probe_rollback(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CINDER_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["validation"]["rollback"] = "NOT_RUN"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("bounded validation" in item or "schema" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_cinder_disk_provisioner_requires_stopped_vm(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.CINDER_DISK_PROVISIONER
            value = path.read_text(encoding="utf-8").replace(
                "$running -contains $resolvedVmx",
                "$false",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("disk provisioner" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_external_input_evidence_rejects_resource_id(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.EXTERNAL_INPUT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["terraform_inputs"]["resource_id"] = "resource-id-redacted"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("external-input" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_external_input_evidence_cannot_record_credential_value(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.EXTERNAL_INPUT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["cloud_profile"]["credential_value_recorded"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("external-input" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_external_input_evidence_cannot_claim_proxy_runtime(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.EXTERNAL_INPUT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["proxy_trust_material"]["proxy_runtime_verified"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("trust material" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_external_input_evidence_cannot_claim_terraform_plan(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.EXTERNAL_INPUT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["execution_boundary"]["terraform_plan_created"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("readiness cannot claim" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_terraform_preflight_cannot_claim_apply(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TERRAFORM_PREFLIGHT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["execution_boundary"]["terraform_apply_executed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("preflight" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_terraform_preflight_rejects_destructive_action(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TERRAFORM_PREFLIGHT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["plan_review"]["expected_changes"][0]["action"] = "delete"
            value["plan_review"]["destructive_action_count"] = 1
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("plan review" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_terraform_preflight_rejects_resource_identifier(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TERRAFORM_PREFLIGHT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["plan_review"]["resource_identifier"] = "resource-id-redacted"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("preflight" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_bounded_deployment_evidence_rejects_resource_address(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.BOUNDED_DEPLOYMENT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["terraform"]["resource_address"] = "192.0.2.10"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("bounded deployment" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_bounded_deployment_evidence_cannot_claim_live_validator(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.BOUNDED_DEPLOYMENT_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["validation_boundary"]["full_live_validator_executed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("live validator" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_host_bootstrap_must_accept_mountpoint_not_mounted_status(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_HOST_ROLE / "tasks/main.yml"
            value = path.read_text(encoding="utf-8").replace("not in [0, 32]", "not in [0, 1]")
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("idempotent dedicated-volume" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_non_secret_config_cannot_be_root_only(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "tasks/main.yml"
            value = path.read_text(encoding="utf-8").replace('mode: "0644"', 'mode: "0640"')
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("Non-secret container configuration" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_validation_playbook_cannot_default_authorize_restart(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATION_PLAYBOOK
            value = path.read_text(encoding="utf-8").replace(
                "zt_vis_002_persistence_restart_authorized: false",
                "zt_vis_002_persistence_restart_authorized: true",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("default-deny restart" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_role_cannot_drop_podman_reboot_restoration(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "tasks/main.yml"
            value = path.read_text(encoding="utf-8").replace(
                "name: podman-restart.service",
                "name: podman.service",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("reboot restoration" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_compose_cannot_use_unsupported_unless_stopped_reboot_policy(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ANSIBLE_ROLE / "templates/compose.yaml.j2"
            value = path.read_text(encoding="utf-8").replace(
                "restart: always",
                "restart: unless-stopped",
                1,
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("Podman-compatible" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_validator_cannot_drop_rollback_marker(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATOR
            value = path.read_text(encoding="utf-8").replace("rollback=PASS", "rollback=UNKNOWN")
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("Live validator" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_validator_cannot_drop_evidence_integrity_marker(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATOR
            value = path.read_text(encoding="utf-8").replace(
                "evidence_integrity=PASS",
                "evidence_integrity=UNKNOWN",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("Live validator" in item for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_evidence_cannot_claim_package_promotion_authority(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["authorization"]["package_status_promotion_authorized"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("promotion" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_evidence_cannot_drop_temporary_access_cleanup(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["cleanup"]["controller_private_keys_removed"] = False
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("cleanup" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_evidence_cannot_hide_rejected_first_attempt(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["execution_attempts"] = value["execution_attempts"][1:]
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("first attempt" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_live_evidence_rejects_runtime_address(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.LIVE_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["infrastructure"]["runtime_address"] = "192.0.2.10"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("live validation evidence" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_partial_promotion_cannot_claim_full_acceptance(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.PARTIAL_PROMOTION_DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["promoted_status"]["runtime_acceptance_status"] = "ACCEPTED"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("promotion" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_partial_promotion_cannot_drop_snapshot_gap(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.PARTIAL_PROMOTION_DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["open_gaps"].remove("FULL_CINDER_SNAPSHOT_REBUILD_AND_REATTACH_RESTORE")
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("open gaps" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_partial_promotion_must_match_live_evidence_hash(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.PARTIAL_PROMOTION_DECISION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["source_evidence"]["sha256"] = "0" * 64
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("hash-bound" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validation_plan_cannot_revert_recorded_live_execution(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATION_PLAN
            value = json.loads(path.read_text(encoding="utf-8"))
            value["execution"]["live_validator_executed"] = False
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("alert validation plan" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validation_evidence_cannot_close_gap_without_status_authority(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["package_boundary"]["alert_gap_closed"] = True
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("alert validation evidence" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validation_evidence_cannot_hide_clock_finding(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATION_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["time_integrity"]["status"] = "PASS"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("clock" in item.lower() or "schema" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validator_requires_grafana_v1_webhook_contract(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATOR
            value = path.read_text(encoding="utf-8").replace('"version": "v1"', '"version": "1"')
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("alert validator" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validation_playbook_cannot_default_authorize_mutation(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATION_PLAYBOOK
            value = path.read_text(encoding="utf-8").replace(
                "zt_vis_002_alert_rule_mutation_authorized: false",
                "zt_vis_002_alert_rule_mutation_authorized: true",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("default-deny" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validator_cannot_bind_wildcard_receiver(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATOR
            value = path.read_text(encoding="utf-8").replace(
                "ThreadingHTTPServer((gateway, 0), Handler)",
                'ThreadingHTTPServer(("0.0.0.0", 0), Handler)',
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("alert validator" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validator_cannot_use_removed_receiver_test_api(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATOR
            value = path.read_text(encoding="utf-8").replace(
                "/apis/notifications.alerting.grafana.app/v1beta1/namespaces/default/receivers/-/test",
                "/api/alertmanager/grafana/config/api/v1/receivers/test",
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("alert validator" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_alert_validator_cannot_drop_cleanup_marker(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.ALERT_VALIDATOR
            value = path.read_text(encoding="utf-8").replace(
                'markers.append("cleanup=PASS")',
                'markers.append("cleanup=UNKNOWN")',
            )
            path.write_text(value, encoding="utf-8")
            self.assertTrue(any("alert validator" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()

    def test_provider_lock_requires_cross_platform_hashes(self) -> None:
        temporary, root = self.copied_root()
        try:
            path = root / artifacts.TF_ENV / ".terraform.lock.hcl"
            value = path.read_text(encoding="utf-8")
            first_hash = '    "h1:MVSoVvhjbu7s1pfYfsiYED8A++XfAoyOlSX1x9PW68E=",\n'
            path.write_text(value.replace(first_hash, ""), encoding="utf-8")
            self.assertTrue(any("provider lock" in item.lower() for item in artifacts.validate(root)))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
