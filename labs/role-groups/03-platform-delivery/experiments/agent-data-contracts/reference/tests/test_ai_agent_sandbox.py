"""Regression and negative tests for the Project Mini-Ona contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_ai_agent_sandbox as sandbox  # noqa: E402


def copied_root() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    for relative in sandbox.REQUIRED_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return temporary, root


class AiAgentSandboxTests(unittest.TestCase):
    def mutate(self, callback) -> list[str]:
        temporary, root = copied_root()
        try:
            path = root / sandbox.CONTRACT
            data = json.loads(path.read_text(encoding="utf-8"))
            callback(data)
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            return sandbox.validate(root).failures
        finally:
            temporary.cleanup()

    def test_current_contract_is_valid(self) -> None:
        self.assertFalse(sandbox.validate(ROOT).failures)

    def test_plain_container_boundary_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["sandbox"].update({"plain_runc_accepted": True}))
        self.assertTrue(any("plain_runc_accepted" in item for item in failures))

    def test_direct_main_push_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["git_delivery"].update({"direct_main_push": True}))
        self.assertTrue(any("direct main push" in item for item in failures))

    def test_missing_cost_budget_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["budgets"]["hard_limits_required"].remove("MONETARY_COST"))
        self.assertTrue(any("hard-budget" in item for item in failures))

    def test_pod_as_durable_authority_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["execution_model"].update({"pod_is_durable_authority": True}))
        self.assertTrue(any("durable job authority" in item for item in failures))

    def test_source_telemetry_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["observability"].update({"source_code_allowed": True}))
        self.assertTrue(any("source_code_allowed" in item for item in failures))

    def test_missing_approval_gate_is_rejected(self) -> None:
        failures = self.mutate(lambda data: data["human_in_the_loop"]["approval_required"].remove("INFRASTRUCTURE_MUTATION"))
        self.assertTrue(any("approval gates" in item for item in failures))

    def test_general_vm_sudo_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / sandbox.VM_BOOTSTRAP
            text = path.read_text(encoding="utf-8").replace(
                "groups: [adm, users]", "groups: [adm, sudo, users]"
            )
            path.write_text(text, encoding="utf-8")
            failures = sandbox.validate(root).failures
            self.assertTrue(any("sudo-group" in item for item in failures))
        finally:
            temporary.cleanup()

    def test_untagged_kata_image_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / sandbox.KATA_VALUES
            text = path.read_text(encoding="utf-8").replace(
                "quay.io/kata-containers/kata-deploy@sha256:460128eea49aee30fd023f1eabd94dc75fd694dff9a09ed82daeba5c126b2b0e",
                "quay.io/kata-containers/kata-deploy:4.0.0",
            )
            path.write_text(text, encoding="utf-8")
            failures = sandbox.validate(root).failures
            self.assertTrue(any("kata-deploy@sha256" in item for item in failures))
        finally:
            temporary.cleanup()

    def test_live_validator_image_digest_tamper_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / sandbox.VM_BOOTSTRAP
            text = path.read_text(encoding="utf-8").replace(
                "docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f",
                "docker.io/library/busybox:latest",
            )
            path.write_text(text, encoding="utf-8")
            failures = sandbox.validate(root).failures
            self.assertTrue(any("busybox@sha256" in item for item in failures))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
