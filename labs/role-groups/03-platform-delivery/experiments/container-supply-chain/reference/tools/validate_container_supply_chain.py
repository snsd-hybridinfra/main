#!/usr/bin/env python3
"""Read-only validator for the IDP container build and k3s delivery chain."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "applications/internal-iaas-portal/supply-chain/container_pipeline.py"
LOCK = ROOT / "applications/internal-iaas-portal/supply-chain/container-supply-chain-lock.json"
AUTHORITY = ROOT / "docs/platform/container-supply-chain.yaml"
DECISION = ROOT / "docs/adr/0023-container-image-supply-chain-and-k3s-delivery.md"
WORKFLOW = ROOT / ".github/workflows/idp-container-supply-chain.yml"
COMPOSE = ROOT / "applications/internal-iaas-portal/compose.mvp.yaml"
GITOPS_APPLICATION = ROOT / "applications/internal-iaas-portal/kubernetes/gitops/idp-container-release-application.yaml"
GITOPS_ROOT = ROOT / "applications/internal-iaas-portal/kubernetes/releases/kustomization.yaml"
RUNNER_REQUIREMENTS = ROOT / "applications/internal-iaas-portal/supply-chain/runner-requirements.json"
RUNTIME_READINESS = ROOT / "docs/platform/container-supply-chain-runtime-readiness.yaml"
RUNNER_PROVISIONER = ROOT / "tools/local-vm/New-IdpSupplyChainRunnerVm.ps1"
RUNNER_BUNDLE_SCHEMA = ROOT / "schemas/idp-runner-bundle-manifest.schema.json"
RUNNER_README = ROOT / "applications/internal-iaas-portal/supply-chain/README.md"
RUNNER_BUNDLE_BUILDER = ROOT / "tools/supply-chain/Build-IdpSupplyChainRunnerBundle.ps1"
RUNNER_BUNDLE_SOURCE_LOCK = ROOT / "applications/internal-iaas-portal/supply-chain/runner-bundle-source-lock.json"
RUNNER_BUNDLE_INSTALLER = ROOT / "applications/internal-iaas-portal/supply-chain/runner-bundle/install.sh"
RUNNER_EGRESS_APPLY = ROOT / "applications/internal-iaas-portal/supply-chain/runner-bundle/idp-egress-policy-apply"
RUNNER_EGRESS_CHECK = ROOT / "applications/internal-iaas-portal/supply-chain/runner-bundle/idp-egress-policy-check"
RUNTIME_REQUIREMENTS = ROOT / "applications/internal-iaas-portal/requirements-runtime.txt"
TERRAFORM_RUNNER_DOCKERFILE = ROOT / "applications/internal-iaas-portal/services/terraform-runner/Dockerfile"
PYTHON_SERVICE_DOCKERFILES = (
    ROOT / "applications/internal-iaas-portal/services/request-api/Dockerfile",
    ROOT / "applications/internal-iaas-portal/services/approval-api/Dockerfile",
    ROOT / "applications/internal-iaas-portal/services/grant-api/Dockerfile",
    TERRAFORM_RUNNER_DOCKERFILE,
)


def _module():
    spec = importlib.util.spec_from_file_location("idp_container_pipeline", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError("container pipeline module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    paths = [
        root / AUTHORITY.relative_to(ROOT),
        root / DECISION.relative_to(ROOT),
        root / LOCK.relative_to(ROOT),
        root / PIPELINE.relative_to(ROOT),
        root / WORKFLOW.relative_to(ROOT),
        root / COMPOSE.relative_to(ROOT),
        root / GITOPS_APPLICATION.relative_to(ROOT),
        root / GITOPS_ROOT.relative_to(ROOT),
        root / RUNNER_REQUIREMENTS.relative_to(ROOT),
        root / RUNTIME_READINESS.relative_to(ROOT),
        root / RUNNER_PROVISIONER.relative_to(ROOT),
        root / RUNNER_BUNDLE_SCHEMA.relative_to(ROOT),
        root / RUNNER_README.relative_to(ROOT),
        root / RUNNER_BUNDLE_BUILDER.relative_to(ROOT),
        root / RUNNER_BUNDLE_SOURCE_LOCK.relative_to(ROOT),
        root / RUNNER_BUNDLE_INSTALLER.relative_to(ROOT),
        root / RUNNER_EGRESS_APPLY.relative_to(ROOT),
        root / RUNNER_EGRESS_CHECK.relative_to(ROOT),
        root / RUNTIME_REQUIREMENTS.relative_to(ROOT),
        *(root / path.relative_to(ROOT) for path in PYTHON_SERVICE_DOCKERFILES),
    ]
    for path in paths:
        if not path.is_file():
            failures.append(f"required authority missing: {path.relative_to(root)}")
    if failures:
        return failures

    try:
        authority = json.loads((root / AUTHORITY.relative_to(ROOT)).read_text(encoding="utf-8"))
        lock = json.loads((root / LOCK.relative_to(ROOT)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"authority parse failed: {exc}"]

    expected_authority = {
        "decision": "docs/adr/0023-container-image-supply-chain-and-k3s-delivery.md",
        "lock": "applications/internal-iaas-portal/supply-chain/container-supply-chain-lock.json",
        "validator": "tools/validate_container_supply_chain.py",
        "pipeline": "applications/internal-iaas-portal/supply-chain/container_pipeline.py",
        "workflow": ".github/workflows/idp-container-supply-chain.yml",
        "runner_requirements": "applications/internal-iaas-portal/supply-chain/runner-requirements.json",
        "runner_provisioner": "tools/local-vm/New-IdpSupplyChainRunnerVm.ps1",
        "runner_bundle_schema": "schemas/idp-runner-bundle-manifest.schema.json",
        "runner_bundle_builder": "tools/supply-chain/Build-IdpSupplyChainRunnerBundle.ps1",
        "runner_bundle_source_lock": "applications/internal-iaas-portal/supply-chain/runner-bundle-source-lock.json",
        "runtime_readiness": "docs/platform/container-supply-chain-runtime-readiness.yaml",
    }
    if authority.get("authority") != expected_authority:
        failures.append("container supply-chain authority paths are not exact")
    status = authority.get("status", {})
    if any(status.get(key) != "NOT_VALIDATED" for key in ("registry_publish", "gitops_promotion", "k3s_installation")):
        failures.append("unvalidated publish/install status was promoted")
    if authority.get("separation", {}).get("terraform_role") != "PROVISION_OPENSTACK_AND_K3S_SERVICE_PLANE":
        failures.append("Terraform/container responsibility separation is missing")
    expected_catalog_packaging = {
        "build_context": "idp-platform-authorities",
        "packaged_authorities": ["composite-service-catalog.yaml", "catalog.json"],
        "source_checkout_authority": "CANONICAL_REPOSITORY_PATH",
        "image_authority": "PACKAGE_LOCAL_READ_ONLY_COPY",
        "missing_or_tampered_behavior": "READINESS_AND_PORTAL_FAIL_CLOSED_503",
        "runtime_validation_status": "NOT_VALIDATED",
    }
    if authority.get("request_api_catalog_packaging") != expected_catalog_packaging:
        failures.append("request-api catalog packaging contract is not exact")
    if lock.get("source", {}).get("repository") != "snsd-hybridinfra/snsd-multicloud-ops":
        failures.append("container source repository does not match the canonical GitHub location")

    try:
        module = _module()
        module.validate_lock(lock, root / "applications/internal-iaas-portal")
    except Exception as exc:  # validator must turn all malformed authorities into a finding
        failures.append(f"container lock policy failed: {exc}")

    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")
    required_tokens = (
        "persist-credentials: false",
        "id-token: write",
        "idp-container-publish",
        "build-release",
        "promote",
        "gh pr create --draft",
        "pull-requests: write",
        "packages: write",
        "docker login ghcr.io",
        "GHCR_TOKEN: ${{ github.token }}",
    )
    for token in required_tokens:
        if token not in workflow:
            failures.append(f"workflow gate is missing: {token}")
    if "@master" in workflow or "@main" in workflow or "docker/login-action" in workflow:
        failures.append("workflow contains mutable action or stored registry-login path")
    if "kubectl" in workflow or "IDP_LIVE_INSTALL_AUTHORIZED" in workflow:
        failures.append("CI must not receive kubeconfig or mutate the cluster directly")

    pipeline = (root / PIPELINE.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in (
        "--sbom=true",
        "--provenance=mode=max",
        "verify-attestation",
        "maximum_high_vulnerabilities",
        "promote_release",
        "GITOPS_PROMOTION_PR_THEN_ARGOCD_RECONCILE",
        "IDP_TOOL_DOCKER_BUILDX_SHA256",
        "IDP_COSIGN_CERTIFICATE_IDENTITY",
        "IDP_COSIGN_CERTIFICATE_OIDC_ISSUER",
        "SYFT_CHECK_FOR_APP_UPDATE",
    ):
        if token not in pipeline:
            failures.append(f"pipeline enforcement is missing: {token}")
    if "kubectl" in pipeline or "install_release" in pipeline:
        failures.append("pipeline contains a forbidden direct cluster install path")
    for token in (
        "_catalog_context_args",
        "--build-context",
        "idp-platform-authorities",
        "git+https://github.com/snsd-hybridinfra/snsd-multicloud-ops",
    ):
        if token not in pipeline:
            failures.append(f"request-api catalog packaging enforcement is missing: {token}")
    compose = (root / COMPOSE.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in ("additional_contexts:", "idp-platform-authorities: ../../docs/platform"):
        if token not in compose:
            failures.append(f"compose catalog build context is missing: {token}")
    if re.search(r"^\s+COSIGN_(?:CERTIFICATE_IDENTITY|OIDC_ISSUER):", workflow, re.MULTILINE):
        failures.append("Cosign verification policy must not override signing service environment")
    provisioner = (root / RUNNER_PROVISIONER.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in (
        "expectedImageSha256",
        "idp-runner-dispatch",
        "--jitconfig",
        "idp-egress-policy-check --strict",
        "IDP_TOOL_DOCKER_BUILDX_SHA256",
        "kubeconfig must not exist",
        "New-RunnerBundleIso",
        'deviceType = "cdrom-image"',
        'SSH_ORIGINAL_COMMAND:-}" == "proxy-denials"',
    ):
        if token not in provisioner:
            failures.append(f"runner provisioner gate is missing: {token}")
    try:
        source_lock = json.loads((root / RUNNER_BUNDLE_SOURCE_LOCK.relative_to(ROOT)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"runner bundle source lock parse failed: {exc}")
    else:
        source_ids = {item.get("id") for item in source_lock.get("sources", [])}
        if source_ids != {"actions-runner", "cosign", "docker", "docker-buildx", "gh", "git", "syft", "trivy"}:
            failures.append("runner bundle source set is not exact")
        for item in source_lock.get("sources", []):
            if not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                failures.append(f"runner source digest is invalid: {item.get('id')}")
    installer = (root / RUNNER_BUNDLE_INSTALLER.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in (
        "no-new-privileges",
        "squid.service",
        "usermod -a -G docker,proxy idprunner",
        "actions-runner.tar.gz",
        "172.17.0.0/16",
        "172.18.0.0/16",
        ".pypi.org",
        ".pythonhosted.org",
        "mirror.gcr.io",
        "dl-cdn.alpinelinux.org",
        "github_results dstdom_regex -i ^productionresultssa[0-9]+[.]blob[.]core[.]windows[.]net$",
        "http_access allow local_runner connect ssl_ports github_results",
        "squid -k parse",
        "systemctl restart squid.service",
    ):
        if token not in installer:
            failures.append(f"runner bundle installer gate is missing: {token}")
    for token in ("--skip-version-check", "--disable-telemetry"):
        if token not in pipeline:
            failures.append(f"Trivy network-minimization gate is missing: {token}")
    for token in ("_sanitized_blocking_findings", "sanitized_vulnerability_gate_denied"):
        if token not in pipeline:
            failures.append(f"sanitized vulnerability diagnostic is missing: {token}")
    if "dstdomain .blob.core.windows.net" in installer:
        failures.append("generic Azure Blob egress must remain denied")
    runtime_requirements = (root / RUNTIME_REQUIREMENTS.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in ("kubernetes>=36.0.3,<37", "urllib3>=2.7.0,<3"):
        if token not in runtime_requirements:
            failures.append(f"remediated runtime dependency is missing: {token}")
    for dockerfile_path in PYTHON_SERVICE_DOCKERFILES:
        dockerfile = (root / dockerfile_path.relative_to(ROOT)).read_text(encoding="utf-8")
        if "apk upgrade --no-cache" not in dockerfile or "apt-get upgrade -y" not in dockerfile:
            failures.append(
                f"base OS security update is missing: {dockerfile_path.relative_to(ROOT)}"
            )
    request_dockerfile = (
        root / "applications/internal-iaas-portal/services/request-api/Dockerfile"
    ).read_text(encoding="utf-8")
    for token in (
        "COPY --from=idp-platform-authorities composite-service-catalog.yaml",
        "COPY terraform/catalog.json /app/request_api/authorities/catalog.json",
    ):
        if token not in request_dockerfile:
            failures.append(f"request-api packaged authority is missing: {token}")
    terraform_runner_dockerfile = (
        root / TERRAFORM_RUNNER_DOCKERFILE.relative_to(ROOT)
    ).read_text(encoding="utf-8")
    if "apk add --no-cache ca-certificates openssh-client" not in terraform_runner_dockerfile:
        failures.append("Alpine-compatible Terraform runner dependency installation is missing")
    egress_apply = (root / RUNNER_EGRESS_APPLY.relative_to(ROOT)).read_text(encoding="utf-8")
    egress_check = (root / RUNNER_EGRESS_CHECK.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in ("-P OUTPUT DROP", "DOCKER-USER", "--dports 443,6443", "--uid-owner"):
        if token not in egress_apply:
            failures.append(f"runner egress apply gate is missing: {token}")
    for token in ("squid.service", "docker.service", "k3s/k3s.yaml", "IDP_DOCKER_EGRESS"):
        if token not in egress_check:
            failures.append(f"runner egress check gate is missing: {token}")
    try:
        schema = json.loads((root / RUNNER_BUNDLE_SCHEMA.relative_to(ROOT)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"runner bundle schema parse failed: {exc}")
    else:
        required_tools = set(schema.get("properties", {}).get("tools", {}).get("required", []))
        if required_tools != {"actions-runner", "cosign", "docker", "docker-buildx", "gh", "git", "syft", "trivy"}:
            failures.append("runner bundle schema tool set is not exact")
    application = (root / GITOPS_APPLICATION.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in ("targetRevision: main", "path: applications/internal-iaas-portal/kubernetes/releases", "prune: false", "selfHeal: true"):
        if token not in application:
            failures.append(f"Argo CD boundary is missing: {token}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="retained for validator interface consistency")
    parser.parse_args(argv)
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: container supply-chain authority, seven-image lock, CI/CD gates and k3s install boundary are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
