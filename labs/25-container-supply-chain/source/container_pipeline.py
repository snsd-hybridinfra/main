#!/usr/bin/env python3
"""Fail-closed container release and k3s installation pipeline.

The module deliberately keeps credentials, kubeconfig, raw scanner output and
generated overlays below the ignored runtime root.  Its pure validation and
rendering functions are used by repository tests; live commands remain gated by
external workload identity and explicit environment authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
DEFAULT_LOCK = Path(__file__).with_name("container-supply-chain-lock.json")
GITOPS_ROOT = APP_ROOT / "kubernetes" / "releases"
DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
REGISTRY_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*(?::[0-9]{2,5})?(?:/[a-z0-9._/-]+)?$")


class SupplyChainError(RuntimeError):
    """Policy or execution failure which must stop promotion."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SupplyChainError(f"cannot read JSON authority: {path}") from exc
    if not isinstance(value, dict):
        raise SupplyChainError(f"JSON authority must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _require_digest(value: Any, label: str, *, allow_zero: bool = False) -> str:
    text = str(value or "").lower()
    match = DIGEST_RE.fullmatch(text)
    if not match or (not allow_zero and set(match.group(1)) == {"0"}):
        raise SupplyChainError(f"{label} must be a non-zero SHA-256 digest")
    return text


def _image_map(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    images = lock.get("images")
    if not isinstance(images, list) or not images:
        raise SupplyChainError("image lock must contain a non-empty images list")
    result: dict[str, dict[str, Any]] = {}
    for image in images:
        if not isinstance(image, dict) or not NAME_RE.fullmatch(str(image.get("id", ""))):
            raise SupplyChainError("image lock contains an invalid image identity")
        image_id = str(image["id"])
        if image_id in result:
            raise SupplyChainError(f"duplicate image identity: {image_id}")
        result[image_id] = image
    return result


def validate_lock(lock: dict[str, Any], app_root: Path = APP_ROOT) -> dict[str, Any]:
    """Validate the static build and Kubernetes consumer authority."""

    if lock.get("schema_version") != "1.0.0":
        raise SupplyChainError("unsupported container supply-chain schema")
    if lock.get("status") != "LOCAL_POLICY_AUTHORITY":
        raise SupplyChainError("container lock status is not authoritative")
    if lock.get("source", {}).get("required_branch_for_release") != "main":
        raise SupplyChainError("release branch must remain main")

    expected = {
        "request-api",
        "approval-api",
        "grant-api",
        "terraform-runner",
        "user-portal",
        "admin-portal",
        "edge-gateway",
    }
    images = _image_map(lock)
    if set(images) != expected:
        raise SupplyChainError("container image set differs from the seven approved services")

    consumer_owners: dict[str, str] = {}
    for image_id, image in images.items():
        repository = str(image.get("repository", ""))
        if repository != f"iaas/{image_id}":
            raise SupplyChainError(f"repository identity mismatch for {image_id}")
        dockerfile = app_root / str(image.get("dockerfile", ""))
        if not dockerfile.is_file() or dockerfile.is_symlink():
            raise SupplyChainError(f"approved Dockerfile is unavailable: {image_id}")
        text = dockerfile.read_text(encoding="utf-8")
        if ":latest" in text.lower() or re.search(r"\bADD\s+https?://", text, re.I):
            raise SupplyChainError(f"unsafe Dockerfile source policy: {image_id}")
        if not re.search(r"^\s*USER\s+\S+", text, re.M):
            raise SupplyChainError(f"Dockerfile has no explicit runtime user: {image_id}")

        base_args = image.get("required_base_args")
        if not isinstance(base_args, list) or not base_args:
            raise SupplyChainError(f"base-image argument set is missing: {image_id}")
        first_from = re.search(r"^\s*FROM\s+", text, re.M | re.I)
        if first_from is None:
            raise SupplyChainError(f"Dockerfile has no build stage: {image_id}")
        for arg in base_args:
            declaration = re.search(
                rf"^\s*ARG\s+{re.escape(str(arg))}(?:=|\s*$)", text, re.M
            )
            if declaration is None:
                raise SupplyChainError(f"Dockerfile does not declare {arg}: {image_id}")
            if declaration.start() > first_from.start():
                raise SupplyChainError(
                    f"Dockerfile does not globally declare {arg} before the first FROM: {image_id}"
                )
            if not re.search(rf"^\s*FROM\s+\$\{{{re.escape(str(arg))}\}}", text, re.M):
                raise SupplyChainError(f"Dockerfile does not consume {arg} in FROM: {image_id}")

        rollout = image.get("rollout")
        if not isinstance(rollout, dict) or rollout.get("kind") != "deployment":
            raise SupplyChainError(f"rollout authority is invalid: {image_id}")
        if rollout.get("name") != image_id or not rollout.get("namespace"):
            raise SupplyChainError(f"rollout identity is invalid: {image_id}")

        consumers = image.get("kubernetes_consumers")
        if not isinstance(consumers, list) or not consumers:
            raise SupplyChainError(f"Kubernetes consumer set is missing: {image_id}")
        expected_reference = f"registry.example.com/{repository}@sha256:{'0' * 64}"
        for relative in consumers:
            relative_text = str(relative)
            if relative_text in consumer_owners:
                raise SupplyChainError(f"consumer has multiple image owners: {relative_text}")
            consumer_owners[relative_text] = image_id
            manifest = app_root / relative_text
            if not manifest.is_file() or manifest.is_symlink():
                raise SupplyChainError(f"Kubernetes consumer is unavailable: {relative_text}")
            manifest_text = manifest.read_text(encoding="utf-8")
            if expected_reference not in manifest_text:
                raise SupplyChainError(f"consumer image placeholder mismatch: {relative_text}")
        install_manifests = image.get("install_manifests")
        if (
            not isinstance(install_manifests, list)
            or not install_manifests
            or not set(install_manifests).issubset(set(consumers))
            or any("migration-job.yaml" in str(item) for item in install_manifests)
        ):
            raise SupplyChainError(f"bounded install manifest set is invalid: {image_id}")

    promotion = lock.get("promotion", {})
    if promotion.get("partial_release_allowed") is not False:
        raise SupplyChainError("partial release must remain denied")
    if promotion.get("maximum_high_vulnerabilities") != 0:
        raise SupplyChainError("HIGH vulnerability threshold must remain zero")
    if promotion.get("maximum_critical_vulnerabilities") != 0:
        raise SupplyChainError("CRITICAL vulnerability threshold must remain zero")
    installation = lock.get("installation", {})
    if (
        installation.get("target") != "K3S"
        or installation.get("mode") != "GITOPS_PROMOTION_PR_THEN_ARGOCD_RECONCILE"
        or installation.get("ci_kubeconfig_allowed") is not False
        or installation.get("ci_direct_cluster_mutation_allowed") is not False
        or installation.get("promotion_pull_request_required") is not True
        or installation.get("argocd_source_branch") != "main"
        or installation.get("gitops_root")
        != "applications/internal-iaas-portal/kubernetes/releases"
    ):
        raise SupplyChainError("GitOps-only k3s installation policy is required")

    return {
        "images": len(images),
        "consumers": len(consumer_owners),
        "dockerfiles": {key: _sha256(app_root / item["dockerfile"]) for key, item in images.items()},
    }


def validate_release(
    release: dict[str, Any], lock: dict[str, Any], *, approved_registry: str
) -> dict[str, Any]:
    """Validate immutable release evidence before an overlay is rendered."""

    validate_lock(lock)
    if release.get("schema_version") != "1.0.0":
        raise SupplyChainError("unsupported release schema")
    release_id = str(release.get("release_id", ""))
    if not NAME_RE.fullmatch(release_id):
        raise SupplyChainError("invalid release identity")
    source_commit = str(release.get("source_commit", "")).lower()
    if not SOURCE_RE.fullmatch(source_commit):
        raise SupplyChainError("release source commit must be an exact Git SHA-1")
    if release.get("source_branch") != "main":
        raise SupplyChainError("release must originate from main")

    registry = approved_registry.strip().lower().rstrip("/")
    if not registry or not REGISTRY_RE.fullmatch(registry):
        raise SupplyChainError("approved registry is invalid")
    if str(release.get("registry", "")).lower().rstrip("/") != registry:
        raise SupplyChainError("release registry differs from external approval")

    locked = _image_map(lock)
    records = release.get("images")
    if not isinstance(records, list):
        raise SupplyChainError("release images must be a list")
    actual: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("id") in actual:
            raise SupplyChainError("release contains an invalid or duplicate image")
        actual[str(record.get("id", ""))] = record
    if set(actual) != set(locked):
        raise SupplyChainError("release image set is not exact")

    for image_id, policy in locked.items():
        record = actual[image_id]
        digest = _require_digest(record.get("digest"), f"{image_id} digest")
        expected_ref = f"{registry}/{policy['repository']}@{digest}"
        if record.get("reference") != expected_ref:
            raise SupplyChainError(f"immutable image reference mismatch: {image_id}")
        _require_digest(record.get("sbom_sha256"), f"{image_id} SBOM digest")
        _require_digest(record.get("provenance_sha256"), f"{image_id} provenance digest")
        scan = record.get("vulnerability_scan", {})
        if scan.get("decision") != "PASSED" or scan.get("high") != 0 or scan.get("critical") != 0:
            raise SupplyChainError(f"vulnerability policy failed: {image_id}")
        if record.get("signature") != "VERIFIED":
            raise SupplyChainError(f"signature was not verified: {image_id}")
        if record.get("sbom_attestation") != "VERIFIED":
            raise SupplyChainError(f"SBOM attestation was not verified: {image_id}")
        if record.get("provenance_attestation") != "VERIFIED":
            raise SupplyChainError(f"provenance attestation was not verified: {image_id}")

    return {"release_id": release_id, "source_commit": source_commit, "images": len(actual)}


def render_release(
    release: dict[str, Any], lock: dict[str, Any], output_root: Path, *, approved_registry: str
) -> Path:
    """Render one isolated Kustomize overlay per application and an attestation."""

    summary = validate_release(release, lock, approved_registry=approved_registry)
    target = output_root.resolve()
    inside_repo = REPO_ROOT.resolve() in target.parents
    inside_runtime = ".runtime" in target.parts
    inside_gitops = GITOPS_ROOT.resolve() in (target, *target.parents)
    if target == REPO_ROOT.resolve() or (inside_repo and not inside_runtime and not inside_gitops):
        raise SupplyChainError("resolved release may be written only to runtime or the reviewed GitOps root")
    target.mkdir(parents=True, exist_ok=False)

    canonical = json.dumps(release, indent=2, sort_keys=True) + "\n"
    (target / "immutable-resolved-release.json").write_text(canonical, encoding="utf-8")
    records = {item["id"]: item for item in release["images"]}
    for image_id, policy in _image_map(lock).items():
        component = target / image_id
        component.mkdir()
        digest = records[image_id]["digest"]
        registry = approved_registry.rstrip("/")
        resources = "".join(
            f"  - {os.path.relpath(APP_ROOT / relative, component).replace(chr(92), '/')}\n"
            for relative in policy["install_manifests"]
        )
        content = (
            "apiVersion: kustomize.config.k8s.io/v1beta1\n"
            "kind: Kustomization\n"
            "resources:\n"
            f"{resources}"
            "images:\n"
            f"  - name: registry.example.com/{policy['repository']}\n"
            f"    newName: {registry}/{policy['repository']}\n"
            f"    digest: {digest}\n"
        )
        (component / "kustomization.yaml").write_text(content, encoding="utf-8")
    release_resources = "".join(f"  - {image_id}\n" for image_id in _image_map(lock))
    (target / "kustomization.yaml").write_text(
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        "resources:\n"
        f"{release_resources}",
        encoding="utf-8",
    )
    (target / "INSTALL_ORDER").write_text("\n".join(_image_map(lock)) + "\n", encoding="utf-8")
    (target / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def promote_release(
    release: dict[str, Any], lock: dict[str, Any], gitops_root: Path, *, approved_registry: str
) -> Path:
    """Write reviewed desired state; callers must commit it on a promotion branch."""

    summary = validate_release(release, lock, approved_registry=approved_registry)
    root = gitops_root.resolve()
    if REPO_ROOT.resolve() in root.parents and root != GITOPS_ROOT.resolve():
        raise SupplyChainError("in-repository promotion target differs from the locked GitOps root")
    root.mkdir(parents=True, exist_ok=True)
    release_id = summary["release_id"]
    target = render_release(
        release,
        lock,
        root / release_id,
        approved_registry=approved_registry,
    )
    (root / "kustomization.yaml").write_text(
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        "resources:\n"
        f"  - {release_id}\n",
        encoding="utf-8",
    )
    return target


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = False,
    environment: dict[str, str] | None = None,
) -> str:
    run_environment = os.environ.copy()
    if environment:
        run_environment.update(environment)
    result = subprocess.run(
        command,
        cwd=cwd,
        env=run_environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "command failed").strip()[:500]
        raise SupplyChainError(f"tool failed ({command[0]}): {detail}")
    return (result.stdout or "").strip()


def _approved_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SupplyChainError(f"required tool is unavailable: {name}")
    env_name = f"IDP_TOOL_{name.upper().replace('-', '_')}_SHA256"
    expected = os.getenv(env_name, "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SupplyChainError(f"approved tool digest is missing: {env_name}")
    if _sha256(Path(path)) != f"sha256:{expected}":
        raise SupplyChainError(f"approved tool digest mismatch: {name}")
    return path


def _approved_docker_buildx(docker: str) -> str:
    path = Path(os.getenv("IDP_DOCKER_BUILDX_PATH", ""))
    if not path.is_absolute() or not path.is_file():
        raise SupplyChainError("approved Docker Buildx plugin path is unavailable")
    expected = os.getenv("IDP_TOOL_DOCKER_BUILDX_SHA256", "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SupplyChainError(
            "approved tool digest is missing: IDP_TOOL_DOCKER_BUILDX_SHA256"
        )
    if _sha256(path) != f"sha256:{expected}":
        raise SupplyChainError("approved tool digest mismatch: docker-buildx")
    _run([docker, "buildx", "version"], capture=True)
    return str(path)


def _base_args(policy: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for arg in policy["required_base_args"]:
        env_name = f"IDP_BASE_{arg}"
        value = os.getenv(env_name, "")
        if "@sha256:" not in value or value.endswith("@sha256:" + "0" * 64):
            raise SupplyChainError(f"digest-pinned base image is missing: {env_name}")
        _require_digest("sha256:" + value.rsplit("@sha256:", 1)[1], env_name)
        result.extend(["--build-arg", f"{arg}={value}"])
    return result


def _catalog_context_args(image_id: str, repo_root: Path) -> list[str]:
    if image_id != "request-api":
        return []
    context = repo_root / "docs/platform"
    authority = context / "composite-service-catalog.yaml"
    if (not authority.is_file() or authority.is_symlink()
            or not context.resolve().is_relative_to(repo_root.resolve())):
        raise SupplyChainError("canonical composite catalog build context is unavailable")
    return ["--build-context", f"idp-platform-authorities={context}"]


def _scan_counts(report: dict[str, Any]) -> tuple[int, int]:
    high = critical = 0
    for result in report.get("Results") or []:
        for finding in result.get("Vulnerabilities") or []:
            severity = str(finding.get("Severity", "")).upper()
            high += severity == "HIGH"
            critical += severity == "CRITICAL"
    return high, critical


def _sanitized_blocking_findings(report: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for result in report.get("Results") or []:
        for finding in result.get("Vulnerabilities") or []:
            severity = str(finding.get("Severity", "")).upper()
            if severity not in {"HIGH", "CRITICAL"}:
                continue
            findings.append(
                {
                    "fixed_version": str(finding.get("FixedVersion", "")),
                    "id": str(finding.get("VulnerabilityID", "")),
                    "installed_version": str(finding.get("InstalledVersion", "")),
                    "package": str(finding.get("PkgName", "")),
                    "severity": severity,
                }
            )
    return sorted(
        findings,
        key=lambda item: (
            item["severity"],
            item["id"],
            item["package"],
            item["installed_version"],
        ),
    )


def build_release(lock: dict[str, Any], *, release_id: str, approved_registry: str) -> Path:
    """Build, scan, publish, sign and render an immutable release on a trusted runner."""

    validate_lock(lock)
    if not NAME_RE.fullmatch(release_id):
        raise SupplyChainError("invalid release identity")
    if os.getenv("GITHUB_REF_NAME", "main") != "main":
        raise SupplyChainError("publishing is restricted to main")
    git = _approved_tool("git")
    _approved_tool("gh")
    source_commit = _run([git, "rev-parse", "HEAD"], cwd=REPO_ROOT, capture=True).lower()
    if not SOURCE_RE.fullmatch(source_commit):
        raise SupplyChainError("cannot resolve an exact source commit")
    if _run([git, "status", "--porcelain"], cwd=REPO_ROOT, capture=True):
        raise SupplyChainError("publishing from a dirty source tree is denied")

    registry = approved_registry.lower().rstrip("/")
    if registry != os.getenv("IDP_APPROVED_REGISTRY", "").lower().rstrip("/"):
        raise SupplyChainError("registry does not match the protected runner approval")
    if not REGISTRY_RE.fullmatch(registry):
        raise SupplyChainError("approved registry is invalid")

    docker = _approved_tool("docker")
    _approved_docker_buildx(docker)
    trivy = _approved_tool("trivy")
    syft = _approved_tool("syft")
    cosign = _approved_tool("cosign")
    identity = os.getenv("IDP_COSIGN_CERTIFICATE_IDENTITY", "")
    issuer = os.getenv("IDP_COSIGN_CERTIFICATE_OIDC_ISSUER", "")
    if not identity or not issuer:
        raise SupplyChainError("keyless signature identity policy is unavailable")

    runtime_root = REPO_ROOT / ".runtime" / "container-supply-chain" / release_id
    if runtime_root.exists():
        raise SupplyChainError("release runtime directory already exists")
    runtime_root.mkdir(parents=True)
    records: list[dict[str, Any]] = []

    for image_id, policy in _image_map(lock).items():
        image_root = runtime_root / "artifacts" / image_id
        image_root.mkdir(parents=True)
        repository = f"{registry}/{policy['repository']}"
        tagged = f"{repository}:{source_commit}"
        metadata_path = image_root / "build-metadata.json"
        command = [
            docker,
            "buildx",
            "build",
            "--push",
            "--sbom=true",
            "--provenance=mode=max",
            "--metadata-file",
            str(metadata_path),
            "--file",
            str(APP_ROOT / policy["dockerfile"]),
            "--tag",
            tagged,
            *_base_args(policy),
            *_catalog_context_args(image_id, REPO_ROOT),
            str(APP_ROOT),
        ]
        _run(command, cwd=REPO_ROOT)
        metadata = _load_json(metadata_path)
        digest = _require_digest(metadata.get("containerimage.digest"), f"{image_id} build digest")
        reference = f"{repository}@{digest}"

        scan_path = image_root / "trivy.json"
        _run(
            [
                trivy,
                "image",
                "--skip-version-check",
                "--disable-telemetry",
                "--format",
                "json",
                "--output",
                str(scan_path),
                reference,
            ]
        )
        scan_report = _load_json(scan_path)
        high, critical = _scan_counts(scan_report)
        if high or critical:
            print(
                json.dumps(
                    {
                        "event": "sanitized_vulnerability_gate_denied",
                        "findings": _sanitized_blocking_findings(scan_report),
                        "image_id": image_id,
                    },
                    sort_keys=True,
                )
            )
            raise SupplyChainError(f"vulnerability gate failed for {image_id}: HIGH={high}, CRITICAL={critical}")

        sbom_path = image_root / "sbom.cdx.json"
        _run(
            [syft, reference, "-o", f"cyclonedx-json={sbom_path}"],
            environment={"SYFT_CHECK_FOR_APP_UPDATE": "false"},
        )
        provenance_path = image_root / "provenance.json"
        provenance_path.write_text(
            json.dumps(
                {
                    "buildType": "https://mobyproject.org/buildkit@v1",
                    "builder": {"id": "idp-hardened-buildx-runner"},
                    "invocation": {
                        "configSource": {
                            "uri": "git+https://github.com/snsd-hybridinfra/snsd-multicloud-ops",
                            "digest": {"sha1": source_commit},
                            "entryPoint": policy["dockerfile"],
                        }
                    },
                    "metadata": {"buildFinishedOn": datetime.now(UTC).isoformat()},
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        _run([cosign, "sign", "--yes", reference])
        _run([cosign, "attest", "--yes", "--type", "cyclonedx", "--predicate", str(sbom_path), reference])
        _run([cosign, "attest", "--yes", "--type", "slsaprovenance", "--predicate", str(provenance_path), reference])
        verify_policy = ["--certificate-identity", identity, "--certificate-oidc-issuer", issuer]
        _run([cosign, "verify", *verify_policy, reference], capture=True)
        _run([cosign, "verify-attestation", *verify_policy, "--type", "cyclonedx", reference], capture=True)
        _run([cosign, "verify-attestation", *verify_policy, "--type", "slsaprovenance", reference], capture=True)
        records.append(
            {
                "id": image_id,
                "reference": reference,
                "digest": digest,
                "sbom_sha256": _sha256(sbom_path),
                "provenance_sha256": _sha256(provenance_path),
                "vulnerability_scan": {"decision": "PASSED", "high": 0, "critical": 0},
                "signature": "VERIFIED",
                "sbom_attestation": "VERIFIED",
                "provenance_attestation": "VERIFIED",
            }
        )

    release = {
        "schema_version": "1.0.0",
        "release_id": release_id,
        "source_commit": source_commit,
        "source_branch": "main",
        "registry": registry,
        "images": records,
    }
    attestation_path = runtime_root / "release-attestation.json"
    attestation_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_release(release, lock, runtime_root / "resolved", approved_registry=registry)
    return attestation_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-lock")
    validate = sub.add_parser("validate-release")
    validate.add_argument("--release", type=Path, required=True)
    validate.add_argument("--registry", required=True)
    render = sub.add_parser("render")
    render.add_argument("--release", type=Path, required=True)
    render.add_argument("--registry", required=True)
    render.add_argument("--output", type=Path, required=True)
    build = sub.add_parser("build-release")
    build.add_argument("--release-id", required=True)
    build.add_argument("--registry", required=True)
    promote = sub.add_parser("promote")
    promote.add_argument("--release", type=Path, required=True)
    promote.add_argument("--registry", required=True)
    promote.add_argument("--gitops-root", type=Path, default=GITOPS_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        lock = _load_json(args.lock)
        if args.command == "validate-lock":
            print(json.dumps(validate_lock(lock), sort_keys=True))
        elif args.command == "validate-release":
            print(json.dumps(validate_release(_load_json(args.release), lock, approved_registry=args.registry), sort_keys=True))
        elif args.command == "render":
            print(render_release(_load_json(args.release), lock, args.output, approved_registry=args.registry))
        elif args.command == "build-release":
            print(build_release(lock, release_id=args.release_id, approved_registry=args.registry))
        elif args.command == "promote":
            print(promote_release(_load_json(args.release), lock, args.gitops_root, approved_registry=args.registry))
    except SupplyChainError as exc:
        print(f"DENIED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
