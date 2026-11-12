"""Run the seven role labs against local fixtures and write reviewable evidence."""
import argparse
from datetime import datetime, timezone
from ipaddress import IPv4Network
from itertools import combinations
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys

from check_catalog import GROUP_ROOT, ROOT, check_catalog

LABS = ROOT / "labs"
ROLES = ROOT / GROUP_ROOT
IDC = Path(__file__).with_name("idc.py")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def python(script, *args, exit_code=0):
    result = subprocess.run([sys.executable, script, *args], cwd=ROOT, text=True,
                            capture_output=True, timeout=60)
    if result.returncode != exit_code:
        raise RuntimeError(f"{Path(script).name} exited {result.returncode}: "
                           f"{(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def fabric(out):
    lab = LABS / "10-network-digital-twin"
    python(lab / "validate.py", "--model", lab / "model.json", "--evidence", out / "digital-twin.json")
    rendered = python(IDC, "render", "--check")
    python(IDC, "inventory", "--out", out / "netbox-plan.json")
    reference = ROLES / "01-network-fabric/idc/netbox-inventory.json"
    require(read_json(out / "netbox-plan.json") == read_json(reference), "NetBox inventory drift")
    return {"case": "Digital Twin path matrix, IDC rendered config parity and NetBox plan",
            "configuration_check": rendered}


def cidrs(path, fields):
    assignments = re.findall(r'^([a-z_]+)\s*=\s*"([^"\n]+)"\s*$', path.read_text(), re.MULTILINE)
    selected = [(key, value) for key, value in assignments if key in fields]
    require(len(selected) == len(fields) and set(dict(selected)) == set(fields),
            f"Missing or duplicate CIDR literal in {path}")
    return tuple(IPv4Network(dict(selected)[key]) for key in fields)


def check_address_plan(plan):
    for provider, (parent, first, second) in plan.items():
        require(first.subnet_of(parent) and second.subnet_of(parent) and not first.overlaps(second),
                f"{provider}: subnet placement or overlap")
    for (left, a), (right, b) in combinations(plan.items(), 2):
        require(not a[0].overlaps(b[0]), f"{left} and {right}: address spaces overlap")


def cloud(out):
    shared = LABS / "24-multicloud-network-iac/terraform/envs"
    openstack = LABS / "50-openstack-network-validation/reference/terraform/envs/openstack-network-validation"
    plan = {
        "aws": cidrs(shared / "aws-network-validation/terraform.tfvars.example",
                     ("vpc_cidr", "public_subnet_cidr", "private_subnet_cidr")),
        "azure": cidrs(shared / "azure-network-validation/terraform.tfvars.example",
                       ("vnet_cidr", "public_subnet_cidr", "private_subnet_cidr")),
        "openstack": cidrs(openstack / "terraform.tfvars.example",
                           ("address_plan_cidr", "management_cidr", "private_subnet_cidr")),
    }
    check_address_plan(plan)
    parent, subnet, _ = plan["aws"]
    try:
        check_address_plan({**plan, "aws": (parent, subnet, subnet)})
    except ValueError as error:
        overlap = str(error)
    else:
        raise ValueError("Overlapping subnets accepted")
    write_json(out / "address-plan.json", {name: list(map(str, ranges)) for name, ranges in plan.items()})
    return {"case": "AWS, Azure and OpenStack fixture CIDR placement", "overlap_rejected": overlap}


def platform(out):
    lab = LABS / "27-self-service-request-api"
    runner = LABS / "29-terraform-runner-blueprints/source/terraform"
    resolver = runpy.run_path(str(lab / "source/request_api/blueprints.py"))
    resolve = resolver["resolve_blueprint"]
    resolve.__globals__.update(
        COMPOSITE_CATALOG_PATH=lab / "reference/docs/platform/composite-service-catalog.yaml",
        EXECUTION_PROFILE_PATH=runner / "catalog.json",
    )
    params = {"environment": "DEV", "size": "SMALL", "duration_hours": 8, "purpose": "Synthetic role lab"}
    vm = resolve(blueprint_id="VM_APPLICATION_STACK", **params)
    api = resolve(blueprint_id="API_DEVELOPMENT_STACK", **params)
    module = read_json(runner / "catalog.json")["products"][vm["selected_execution_profile"]]["module_name"]
    require(vm["resolution_status"] == "RESOLVED_LOCAL" and (runner / "modules" / module / "main.tf").is_file(),
            "VM blueprint does not resolve to an available module")
    require(api["resolution_status"] == "BLOCKED_UNIMPLEMENTED_COMPONENTS" and api["blocking_gates"],
            "Incomplete API blueprint must be blocked")
    require(not vm["runtime_authorized"] and not api["runtime_authorized"], "Unexpected execution authorization")
    for manifest in (vm, api):
        actual = manifest["manifest_digest"]
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        require(resolver["canonical_manifest_digest"](unsigned) == actual, "Invalid blueprint digest")
    write_json(out / "blueprints.json", {"vm": vm, "api": api, "vm_module": module})
    return {"case": "VM resolves, API awaits its dependencies, deployment authorization stays false"}


def security(out):
    lab = LABS / "04-iam-sts"
    python(lab / "evaluate_policy.py", "--directory", lab, "--evidence", out / "iam.json")
    return {"case": "IAM/STS trust, scoped allow and explicit deny fixtures"}


def observability(out):
    lab = LABS / "19-metric-anomaly-scoring"
    dataset = lab / "datasets/ml-metric-dataset-synthetic.sample.csv"
    invalid = lab / "datasets/ml-metric-dataset-invalid.sample.csv"
    profile = lab / "models/ml-anomaly-threshold-profile.example.yml"
    normalize = lab / "scripts/metric-dataset-normalization.example.py"
    python(normalize, "--input", dataset)
    python(normalize, "--input", invalid, exit_code=1)
    detection = out / "detection.csv"
    python(lab / "scripts/metric-anomaly-detection.example.py", "--input", dataset,
           "--output", detection, "--profile", profile)
    summary = out / "triage.json"
    python(lab / "scripts/anomaly-report-generation.example.py", "--input", detection,
           "--metadata", profile, "--output", out / "triage.md", "--summary-output", summary)
    require(read_json(summary)["anomaly_count"] > 0, "No anomaly was identified in the fixture")
    return {"case": "Synthetic metric triage and invalid dataset rejection"}


def automation(out):
    lab = LABS / "03-restconf-python"
    reader = runpy.run_path(str(lab / "compare.py"))
    api = reader["api_rows"](read_json(lab / "fixtures/interfaces.json"))
    cli = reader["cli_rows"]((lab / "fixtures/show_interfaces.txt").read_text())
    comparison = reader["compare"](api, cli)
    require(comparison["compared"] == 3 and comparison["mismatches"] == 0
            and not comparison["api_only"] and not comparison["cli_only"], "Interface fixtures diverge")
    write_json(out / "interfaces.json", comparison)
    evaluator = LABS / "21-automation-approval/src/evaluate_action_policy.py"
    allowed = python(evaluator)
    rejected = python(evaluator, "--parameters", '{"path":"../../private"}', exit_code=1)
    require("decision=ALLOW_CHECK" in allowed and "Unsafe parameter value" in rejected,
            "Unexpected policy decisions")
    (out / "policy.txt").write_text(f"{allowed}\n{rejected}\n", encoding="utf-8")
    return {"case": "RESTCONF/CLI fixture parity and read-only change policy"}


def recovery(out):
    python(LABS / "05-backup-recovery/run-lab.py", "--evidence", out / "site-restore.json")
    return {"case": "Loopback HTTP/SQLite site outage, missing snapshot denial and restore"}


CHECKS = {
    "01-network-fabric": fabric, "02-cloud-foundation": cloud, "03-platform-delivery": platform,
    "04-security-trust": security, "05-observability-sre": observability, "06-change-automation": automation,
    "07-recovery-dr": recovery,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("all", *CHECKS))
    parser.add_argument("--out", type=Path, default=ROOT / ".runtime/role-labs")
    args = parser.parse_args()
    catalog = check_catalog(ROOT)
    selected = CHECKS if args.role == "all" else {args.role: CHECKS[args.role]}
    started = datetime.now(timezone.utc)
    run_dir = args.out.resolve() / started.strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir.mkdir(parents=True)
    results = {}
    for role, check in selected.items():
        folder = run_dir / role
        folder.mkdir()
        try:
            results[role] = {"pass": True, **check(folder)}
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            results[role] = {"pass": False, "error": str(error)}
        state = "PASS" if results[role]["pass"] else "FAIL"
        print(f"{state} {role}")
    write_json(run_dir / "summary.json", {
        "timestamp": started.isoformat(timespec="milliseconds"),
        "scope": "local role workflows", "catalog": catalog, "roles": results,
    })
    print(run_dir / "summary.json")
    return 0 if all(row["pass"] for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
