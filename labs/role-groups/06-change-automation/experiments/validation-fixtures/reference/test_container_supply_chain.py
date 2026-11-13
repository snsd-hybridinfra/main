from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "applications/internal-iaas-portal/supply-chain/container_pipeline.py"
LOCK = ROOT / "applications/internal-iaas-portal/supply-chain/container-supply-chain-lock.json"
TEST_RUNTIME = ROOT / ".runtime/unit-tests/container-supply-chain"
EXTERNAL_TEST_RUNTIME = ROOT.parent / ".runtime-tests/snsd-multicloud-ops/container-supply-chain"


def load_pipeline():
    spec = importlib.util.spec_from_file_location("container_pipeline_tested", PIPELINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContainerSupplyChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEST_RUNTIME.mkdir(parents=True, exist_ok=True)
        EXTERNAL_TEST_RUNTIME.mkdir(parents=True, exist_ok=True)
        cls.pipeline = load_pipeline()
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))
        cls.registry = "registry.internal.example"

    def release(self) -> dict:
        images = []
        for index, policy in enumerate(self.lock["images"], 1):
            hex_digest = f"{index:064x}"
            digest = f"sha256:{hex_digest}"
            images.append(
                {
                    "id": policy["id"],
                    "reference": f"{self.registry}/{policy['repository']}@{digest}",
                    "digest": digest,
                    "sbom_sha256": "sha256:" + f"{index + 10:064x}",
                    "provenance_sha256": "sha256:" + f"{index + 20:064x}",
                    "vulnerability_scan": {"decision": "PASSED", "high": 0, "critical": 0},
                    "signature": "VERIFIED",
                    "sbom_attestation": "VERIFIED",
                    "provenance_attestation": "VERIFIED",
                }
            )
        return {
            "schema_version": "1.0.0",
            "release_id": "idp-20260828-01",
            "source_commit": "a" * 40,
            "source_branch": "main",
            "registry": self.registry,
            "images": images,
        }

    def test_current_lock_is_exact_and_locally_valid(self) -> None:
        result = self.pipeline.validate_lock(self.lock)
        self.assertEqual(result["images"], 7)
        self.assertEqual(result["consumers"], 10)

    def test_only_request_image_receives_canonical_catalog_context(self) -> None:
        self.assertEqual(self.pipeline._catalog_context_args("request-api", ROOT),
                         ["--build-context", f"idp-platform-authorities={ROOT / 'docs/platform'}"])
        for image in self.lock["images"]:
            if image["id"] != "request-api":
                self.assertEqual(self.pipeline._catalog_context_args(image["id"], ROOT), [])

    def test_missing_catalog_context_denies_request_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(self.pipeline.SupplyChainError, "catalog build context"):
                self.pipeline._catalog_context_args("request-api", Path(temporary))

    def test_valid_release_renders_digest_only_component_overlays(self) -> None:
        release = self.release()
        with tempfile.TemporaryDirectory(dir=TEST_RUNTIME) as temporary:
            output = Path(temporary) / "resolved"
            self.pipeline.render_release(release, self.lock, output, approved_registry=self.registry)
            files = list(output.glob("*/kustomization.yaml"))
            self.assertEqual(len(files), 7)
            content = "\n".join(path.read_text(encoding="utf-8") for path in files)
            self.assertNotIn(":latest", content)
            self.assertNotIn("sha256:" + "0" * 64, content)
            self.assertEqual(content.count("digest: sha256:"), 7)
            self.assertTrue((output / "kustomization.yaml").is_file())

    def test_promotion_updates_only_reviewed_gitops_pointer(self) -> None:
        release = self.release()
        with tempfile.TemporaryDirectory(dir=EXTERNAL_TEST_RUNTIME) as temporary:
            root = Path(temporary) / "releases"
            target = self.pipeline.promote_release(
                release, self.lock, root, approved_registry=self.registry
            )
            self.assertEqual(target.name, release["release_id"])
            pointer = (root / "kustomization.yaml").read_text(encoding="utf-8")
            self.assertIn(f"- {release['release_id']}", pointer)
            self.assertNotIn("kubectl", pointer)

    def test_partial_release_is_denied(self) -> None:
        release = self.release()
        release["images"].pop()
        with self.assertRaisesRegex(self.pipeline.SupplyChainError, "not exact"):
            self.pipeline.validate_release(release, self.lock, approved_registry=self.registry)

    def test_zero_digest_is_denied(self) -> None:
        release = self.release()
        release["images"][0]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(self.pipeline.SupplyChainError, "non-zero"):
            self.pipeline.validate_release(release, self.lock, approved_registry=self.registry)

    def test_mutated_registry_is_denied(self) -> None:
        release = self.release()
        release["registry"] = "attacker.invalid"
        with self.assertRaisesRegex(self.pipeline.SupplyChainError, "differs"):
            self.pipeline.validate_release(release, self.lock, approved_registry=self.registry)

    def test_high_vulnerability_is_denied(self) -> None:
        release = self.release()
        release["images"][2]["vulnerability_scan"]["high"] = 1
        with self.assertRaisesRegex(self.pipeline.SupplyChainError, "vulnerability"):
            self.pipeline.validate_release(release, self.lock, approved_registry=self.registry)

    def test_blocking_findings_are_sanitized_and_filtered(self) -> None:
        report = {
            "Results": [
                {
                    "Target": "private-target",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-TEST-0001",
                            "PkgName": "example-package",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "1.1",
                            "Severity": "CRITICAL",
                            "Title": "must not be emitted",
                            "Description": "must not be emitted",
                            "PrimaryURL": "https://example.invalid/private",
                        },
                        {
                            "VulnerabilityID": "CVE-TEST-0002",
                            "PkgName": "low-package",
                            "Severity": "LOW",
                        },
                    ],
                }
            ]
        }
        findings = self.pipeline._sanitized_blocking_findings(report)
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            set(findings[0]),
            {"fixed_version", "id", "installed_version", "package", "severity"},
        )
        self.assertEqual(findings[0]["id"], "CVE-TEST-0001")

    def test_unsigned_or_unattested_image_is_denied(self) -> None:
        for field in ("signature", "sbom_attestation", "provenance_attestation"):
            release = self.release()
            release["images"][1][field] = "MISSING"
            with self.assertRaises(self.pipeline.SupplyChainError):
                self.pipeline.validate_release(release, self.lock, approved_registry=self.registry)

    def test_unlocked_dockerfile_or_consumer_is_denied(self) -> None:
        lock = copy.deepcopy(self.lock)
        lock["images"][0]["dockerfile"] = "services/request-api/unknown.Dockerfile"
        with self.assertRaisesRegex(self.pipeline.SupplyChainError, "Dockerfile"):
            self.pipeline.validate_lock(lock)

    def test_stage_scoped_base_argument_is_denied_before_live_build(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_RUNTIME) as temporary:
            app_root = Path(temporary) / "internal-iaas-portal"
            shutil.copytree(
                ROOT / "applications/internal-iaas-portal",
                app_root,
                ignore=shutil.ignore_patterns(".pytest_cache", "__pycache__"),
            )
            dockerfile = app_root / "services/terraform-runner/Dockerfile"
            text = dockerfile.read_text(encoding="utf-8")
            text = text.replace(
                "ARG TERRAFORM_IMAGE=hashicorp/terraform:1.16.1\n"
                "ARG PYTHON_IMAGE=python:3.12-slim\n\n"
                "FROM ${TERRAFORM_IMAGE} AS terraform\n",
                "ARG TERRAFORM_IMAGE=hashicorp/terraform:1.16.1\n"
                "FROM ${TERRAFORM_IMAGE} AS terraform\n\n"
                "ARG PYTHON_IMAGE=python:3.12-slim\n",
            )
            dockerfile.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(
                self.pipeline.SupplyChainError, "before the first FROM"
            ):
                self.pipeline.validate_lock(self.lock, app_root=app_root)

    def test_unapproved_buildx_digest_is_denied(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_RUNTIME) as temporary:
            plugin = Path(temporary) / "docker-buildx"
            plugin.write_bytes(b"reviewed-buildx")
            environment = {
                "IDP_DOCKER_BUILDX_PATH": str(plugin),
                "IDP_TOOL_DOCKER_BUILDX_SHA256": "0" * 64,
            }
            with mock.patch.dict(os.environ, environment, clear=False):
                with self.assertRaisesRegex(
                    self.pipeline.SupplyChainError, "digest mismatch: docker-buildx"
                ):
                    self.pipeline._approved_docker_buildx("docker")

    def test_run_applies_bounded_environment_override(self) -> None:
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(self.pipeline.subprocess, "run", return_value=completed) as run:
            with mock.patch.dict(os.environ, {"PRESERVED_TEST_VALUE": "present"}, clear=False):
                self.pipeline._run(
                    ["reviewed-tool", "scan"],
                    environment={"SYFT_CHECK_FOR_APP_UPDATE": "false"},
                )
        invoked_environment = run.call_args.kwargs["env"]
        self.assertEqual(invoked_environment["PRESERVED_TEST_VALUE"], "present")
        self.assertEqual(invoked_environment["SYFT_CHECK_FOR_APP_UPDATE"], "false")


if __name__ == "__main__":
    unittest.main()
