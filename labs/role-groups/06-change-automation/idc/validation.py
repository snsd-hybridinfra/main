"""Apply an Ansible candidate, validate the lab state and record manual recovery."""
import argparse
from datetime import datetime, timezone
from difflib import unified_diff
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time
from uuid import uuid4

from idc_lab.events import change_event, emit
from idc_lab.model import OUT, ROOT, ROUTERS, STATE, interfaces
from idc_lab.policy import CANDIDATES as POLICIES
from idc_lab.policy import NODE, POLICY_SLOT, policy_commands, running
from idc_lab.runtime import ERRORS, checked_cli, describe, lab_lock, require_ready, vty, vty_args
from idc_lab.verify import check, ports, utc, write_json

HERE = Path(__file__).resolve().parent
DESCRIPTION = "IDC-LAB-U1"
CANDIDATES = ("description", *POLICIES)
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def configs():
    current = {node: running(node) for node in ROUTERS}
    for node, text in current.items():
        if not any(line.strip() == f"bgp router-id {ROUTERS[node]['loopback']}" for line in text.splitlines()):
            raise ValueError(f"FRR identity verification failed on {node}")
    return current


def state():
    result = check()
    result["interfaces"] = {}
    for node in ROUTERS:
        try:
            rows = ports(node)
            for port, *_ in interfaces(node):
                status = rows.get(port, {}).get("operstate", "MISSING")
                result["interfaces"][f"{node}/{port}"] = status
                if status != "UP":
                    result["failures"].append(f"{node}/{port}: interface {status}")
        except ERRORS as error:
            result["failures"].append(f"{node}: interface query: {describe(error)}")
    result["pass"] = not result["failures"]
    return result


def hashes(data):
    return {node: sha256(text.encode()).hexdigest() for node, text in data.items()}


def snapshot(folder, name):
    result, current = state(), configs()
    target = folder / name
    target.mkdir(mode=0o700)
    for node, text in current.items():
        (target / f"{node}.conf").write_text(text, encoding="utf-8")
    result["config_sha256"] = hashes(current)
    write_json(folder / f"{name}.json", result)
    return result, current


def commands(candidate, applying):
    if candidate == "description":
        description = f"description {DESCRIPTION}" if applying else "no description"
        return [["configure terminal", "interface eth1", description]]
    return policy_commands(candidate, applying)


def candidate_only(candidate, before, after):
    old, new = before[NODE], after[NODE]
    lines = new.splitlines()
    if candidate == "description":
        stanza = ["interface eth1", f" description {DESCRIPTION}", "exit"]
        try:
            start = lines.index(stanza[0])
        except ValueError:
            return False
        if lines[start:start + len(stanza)] != stanza:
            return False
        del lines[start:start + len(stanza)]
        if 0 < start < len(lines) and lines[start - 1] == lines[start] == "!":
            del lines[start]
    else:
        setting = policy_commands(candidate, True)[0][-1]
        if lines.count(setting) != 1:
            return False
        lines.remove(setting)
    return new != old and lines == old.splitlines() and all(
        before[node] == after[node] for node in ROUTERS if node != NODE
    )


def compare(before, after):
    """Compare stable state. FRR and the kernel may recreate numeric route handles."""
    changes = []

    def record(check_name, old, new):
        if old != new:
            changes.append({"check": check_name, "before": old, "after": new})

    for group in ("interfaces", "neighbors", "probes"):
        for key, value in before[group].items():
            record(f"{group}/{key}", value, after[group].get(key))
    for node, leaf in before["leaves"].items():
        actual = after["leaves"].get(node) or {}
        for field in ("next_hops", "imet", "remote_mac", "l3vni", "underlay_isolated"):
            record(f"leaves/{node}/{field}", leaf[field], actual.get(field))
        keys = ("dst", "gateway", "dev", "protocol")
        old = sorted([row[key] for key in keys] for row in leaf["tenant_routes"])
        new = sorted([row[key] for key in keys] for row in actual.get("tenant_routes", []))
        record(f"leaves/{node}/tenant_routes", old, new)
    return changes


def diff_configs(folder, before, after):
    diff = "".join(
        "".join(unified_diff(before[node].splitlines(keepends=True), after[node].splitlines(keepends=True),
                             fromfile=f"before/{node}.conf", tofile=f"after/{node}.conf"))
        for node in ROUTERS
    )
    (folder / "config.diff").write_text(diff, encoding="utf-8")
    return [node for node in ROUTERS if before[node] != after[node]]


def report(folder, result, recovery=False):
    stem = "recovery-result" if recovery else "result"
    write_json(folder / f"{stem}.json", result)
    lines = ["# 네트워크 변경 검증", "", f"- 실행 · {result['run']} · {result['candidate']}",
             f"- 단계와 결과 · {result['phase']} · {result['status']}",
             f"- 변경 장비 · {', '.join(result['changed_devices']) or '없음'}",
             f"- 검사 시각 UTC · {result['timestamp']}", ""]
    lines += [f"- {failure}" for failure in result["failures"]]
    for drift in result["state_changes"]:
        lines.append(f"- {drift['check']} · {json.dumps(drift['before'])} → {json.dumps(drift['after'])}")
    lines += ["", f"[검증 JSON]({stem}.json)"]
    if (folder / "RECOVERY.md").is_file():
        lines.append("[수동 복구 절차](RECOVERY.md)")
    (folder / ("RECOVERY-RESULT.md" if recovery else "REPORT.md")).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def recovery_guide(folder, candidate):
    inverse = ["sudo " + shlex.join([*vty_args(NODE), *(word for cmd in group for word in ("-c", cmd))])
               for group in commands(candidate, False)]
    text = [
        "# 수동 원복 절차", "", "1. 현재 설정과 이 실행의 before/ 백업·config.diff를 대조합니다.",
        "2. 전용 랩에서 후보 항목의 역명령을 실행합니다.", "", "```" + "sh",
        *inverse, "```", "", "3. 원복 후 구성과 네트워크 기준선을 다시 검증합니다.", "",
        "```" + "sh", "sudo python3 tools/idc.py change-validate verify-recovery --run-dir "
        + shlex.quote(str(folder)), "```", "",
    ]
    (folder / "RECOVERY.md").write_text("\n".join(text), encoding="utf-8")


def result_for(folder, candidate, phase, status, failures=(), changes=(), devices=()):
    return {"schema_version": 1, "timestamp": utc(), "run": folder.name, "candidate": candidate,
            "phase": phase, "status": status, "failures": list(failures),
            "state_changes": list(changes), "changed_devices": list(devices)}


def context(folder, candidate):
    return {"run": folder.name, "node": NODE, "candidate": candidate,
            "interface": "eth1" if candidate == "description" else None}


def ansible_change(folder, candidate):
    spec = folder / "change-input.json"
    write_json(spec, {
        "idc_change_target": NODE,
        "idc_change_vty": list(vty_args(NODE)),
        "idc_change_groups": [[part for cmd in group for part in ("-c", cmd)]
                              for group in commands(candidate, True)],
    })
    command = [sys.executable, "-m", "ansible.cli.playbook", "-i", str(HERE / "inventory.ini"),
               str(HERE / "apply-change.yml"), "-e", f"@{spec}"]
    with (folder / "ansible.log").open("w", encoding="utf-8") as output:
        completed = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=100)
    if completed.returncode:
        raise RuntimeError(f"Ansible exited {completed.returncode}. See ansible.log.")


def occupied(candidate, leaf_config):
    return ("interface eth1" in leaf_config.splitlines() if candidate == "description"
            else POLICY_SLOT + " " in leaf_config)


def apply(folder, candidate):
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_json(folder / "request.json", {"run": folder.name, "candidate": candidate,
                                       "fabric_id": (STATE / "ready").read_text().strip()})
    phase = "precheck"
    try:
        before, old = snapshot(folder, "before")
        failures = list(before["failures"])
        if occupied(candidate, old[NODE]):
            failures.append("Leaf1 change slot is occupied.")
        if failures:
            return result_for(folder, candidate, phase, "BLOCKED", failures)
        recovery_guide(folder, candidate)
        phase = "apply"
        change_event("change_issued", **context(folder, candidate))
        ansible_change(folder, candidate)
        change_event("change_applied", **context(folder, candidate))
        phase = "postcheck"
        # Give the inbound soft refresh time to reach the kernel before sampling.
        time.sleep(2)
        after, current = snapshot(folder, "after")
        devices = diff_configs(folder, old, current)
        changes = compare(before, after)
        failures = list(after["failures"])
        if not candidate_only(candidate, old, current):
            failures.append("Running configuration differs from the expected candidate.")
        failures += [f"{row['check']}: differs from the baseline" for row in changes]
        return result_for(folder, candidate, phase, "FAIL" if failures else "PASS", failures, changes, devices)
    except (*ERRORS, KeyError, KeyboardInterrupt) as error:
        return result_for(folder, candidate, phase, "BLOCKED" if phase == "precheck" else "FAIL",
                          [describe(error) or "Interrupted. Inspect the current configuration."])


def read_request(folder):
    request = json.loads((folder / "request.json").read_text())
    if request["candidate"] not in CANDIDATES or request["run"] != folder.name or not ID.fullmatch(folder.name):
        raise ValueError("Invalid recovery run.")
    fabric = (STATE / "ready").read_text().strip()
    if not fabric or fabric != request["fabric_id"]:
        raise ValueError("This change was recorded on a different lab runtime.")
    if not (folder / "RECOVERY.md").is_file():
        raise ValueError("The change was blocked before apply.")
    return request["candidate"]


def read_backup(folder, before):
    backup = {node: (folder / "before" / f"{node}.conf").read_text() for node in ROUTERS}
    if hashes(backup) != before["config_sha256"]:
        raise ValueError("The configuration backup no longer matches its snapshot hashes.")
    return backup


def recover(folder, execute):
    candidate = read_request(folder)
    before = json.loads((folder / "before.json").read_text())
    backup = read_backup(folder, before)
    if execute:
        current = configs()
        if current != backup:
            if not candidate_only(candidate, backup, current):
                raise RuntimeError("Current configuration is outside this change scope. See RECOVERY.md.")
            for group in commands(candidate, False):
                checked_cli(vty(NODE, *group, timeout=8))
            change_event("restore_applied", **context(folder, candidate))
    deadline = time.monotonic() + 30
    while not state()["pass"] and time.monotonic() < deadline:
        time.sleep(0.7)
    name = datetime.now(timezone.utc).strftime("recovery-%Y%m%dT%H%M%S%fZ")
    after, current = snapshot(folder, name)
    changes = compare(before, after)
    devices = [node for node in ROUTERS if current[node] != backup[node]]
    failures = [*after["failures"], *(f"{row['check']}: differs from the baseline" for row in changes),
                *(f"{node}: configuration does not match backup" for node in devices)]
    return result_for(folder, candidate, name, "FAIL" if failures else "PASS", failures, changes, devices)


def interrupt(*_):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("candidate", choices=CANDIDATES)
    apply_parser.add_argument("--id")
    apply_parser.add_argument("--out", type=Path, default=OUT / "operations/changes")
    for action in ("restore", "verify-recovery"):
        sub.add_parser(action).add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupt)
    try:
        with lab_lock():
            require_ready()
            if not (STATE / "ready").read_text().strip():
                raise ValueError("Restart the lab fabric to initialize its runtime ID.")
            if args.action == "apply":
                run_id = args.id or args.candidate + "-" + uuid4().hex[:8]
                if not ID.fullmatch(run_id):
                    raise ValueError("Change ID must be a lowercase slug of up to 64 characters.")
                folder = args.out.resolve() / run_id
                result = apply(folder, args.candidate)
                report(folder, result)
                fields = {**context(folder, args.candidate), "status": result["status"]}
                change_event("change_checked", **fields)
                if result["status"] != "PASS":
                    emit(NODE, "change-validation", json.dumps({**fields, "event": "validation_failed",
                                                                "failed_checks": len(result["failures"])}))
                path = folder / "REPORT.md"
            else:
                folder = args.run_dir.resolve()
                result = recover(folder, args.action == "restore")
                report(folder, result, recovery=True)
                path = folder / "RECOVERY-RESULT.md"
    except (*ERRORS, KeyError, TypeError, KeyboardInterrupt) as error:
        parser.exit(1, (describe(error) or "Interrupted.") + "\n")
    output = sys.stdout if result["status"] == "PASS" else sys.stderr
    print(f"[{result['status']}] {path}", file=output)
    for failure in result["failures"]:
        print(f"- {failure}", file=output)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
