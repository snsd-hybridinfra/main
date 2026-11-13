#!/usr/bin/env python3
"""Validate fail-closed container supply-chain runtime readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READINESS = Path("docs/platform/container-supply-chain-runtime-readiness.yaml")
RUNNER = Path("applications/internal-iaas-portal/supply-chain/runner-requirements.json")


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        readiness = json.loads((root / READINESS).read_text(encoding="utf-8"))
        runner = json.loads((root / RUNNER).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"runtime readiness authority cannot be read: {exc}"]
    if readiness.get("status") != "BLOCKED_EXTERNAL_INPUTS" or readiness.get("runtime_claim") != "NOT_VALIDATED":
        failures.append("container runtime readiness was promoted without evidence")
    github = readiness.get("github", {})
    if github.get("self_hosted_runners_total") != 0 or github.get("matching_online_runner_count") != 0:
        failures.append("recorded GitHub runner discovery no longer matches the blocked snapshot")
    if github.get("required_action_variables_present") != 0 or github.get("required_action_variables_total") != 13:
        failures.append("recorded GitHub variable discovery is not exact")
    if any(readiness.get("status_credit", {}).values()):
        failures.append("blocked readiness must grant no runtime or security status credit")
    local_preparation = readiness.get("local_runner_preparation", {})
    if (
        local_preparation.get("provisioner") != "LOCAL_VALIDATED"
        or local_preparation.get("reviewed_ubuntu_image") != "SHA256_VERIFIED_PRESENT"
        or local_preparation.get("dedicated_vm_target") != "ABSENT"
        or local_preparation.get("reviewed_runner_bundle") != "NOT_PREPARED"
        or local_preparation.get("dedicated_dispatch_key") != "NOT_PREPARED"
    ):
        failures.append("local runner preparation snapshot is inconsistent")
    expected_blockers = {
        "HARDENED_EPHEMERAL_LINUX_RUNNER",
        "APPROVED_PRIVATE_REGISTRY_AND_WORKLOAD_IDENTITY",
        "DIGEST_PINNED_BASE_IMAGES",
        "DIGEST_APPROVED_BUILD_SCAN_SIGN_TOOLCHAIN",
        "GITHUB_PROTECTED_PUBLISH_ENVIRONMENT",
        "GITHUB_ACTION_VARIABLES",
        "ARGOCD_BOOTSTRAP_ON_APPROVED_K3S",
    }
    if set(readiness.get("external_blockers", [])) != expected_blockers:
        failures.append("external blocker set is incomplete")
    runner_policy = runner.get("runner", {})
    if (
        runner.get("status") != "REQUIRED_NOT_PROVISIONED"
        or runner_policy.get("ephemeral_registration_required") is not True
        or runner_policy.get("maximum_jobs_per_registration") != 1
        or runner_policy.get("kubeconfig_allowed") is not False
    ):
        failures.append("hardened ephemeral runner policy changed")
    tools = {item.get("name"): item.get("sha256_environment") for item in runner.get("toolchain", [])}
    if set(tools) != {"docker", "docker-buildx", "trivy", "syft", "cosign", "git", "gh"}:
        failures.append("approved runner tool set is not exact")
    buildx = next((item for item in runner.get("toolchain", []) if item.get("name") == "docker-buildx"), {})
    if buildx.get("path") != "/usr/local/lib/docker/cli-plugins/docker-buildx":
        failures.append("Docker Buildx plugin path is not exact")
    if runner.get("network", {}).get("kubernetes_api_egress_allowed") is not False:
        failures.append("CI runner must not reach the Kubernetes API")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.parse_args()
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: container runtime readiness remains fail-closed on seven external prerequisites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
