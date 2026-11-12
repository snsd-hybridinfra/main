"""Inject one synthetic IDC fault, restore the baseline and record measurements."""
import argparse
import csv
import json
from pathlib import Path
import signal
from threading import Event, Thread
import time
from uuid import uuid4

from idc_lab.events import event
from idc_lab.model import OUT, ROUTERS, STATE, interfaces
from idc_lab.policy import ASN, BASE_HOPS, NODE, REMOTE, SPINE1, SPINE2
from idc_lab.policy import change_policy, config, require_free_slot
from idc_lab.runtime import ERRORS, describe, lab_lock, link_state, processes, require_ready
from idc_lab.runtime import start_router, stop_processes
from idc_lab.verify import http, next_hops, peer_states, ping, ports, utc, wait_healthy, write_json

FAULTS = {"spine-link": 1, "bgp-neighbor": 1, "ecmp-path": 1, "leaf-device": 0, "routing-policy": 0}
INTERVAL = 0.25
REQUIRED = 3


def apply_fault(name, apply):
    if name == "spine-link":
        link_state(NODE, "eth1", "down" if apply else "up")
    elif name == "bgp-neighbor":
        command = f"neighbor {SPINE1} shutdown"
        config(f"router bgp {ASN}", command if apply else "no " + command)
    elif name == "ecmp-path":
        config(f"router bgp {ASN}", "address-family ipv4 unicast", f"maximum-paths {1 if apply else 2}")
    elif name == "leaf-device":
        if not apply:
            stop_processes("leaf2")
        for port, *_ in interfaces("leaf2"):
            link_state("leaf2", port, "down" if apply else "up")
        (stop_processes if apply else start_router)("leaf2")
    elif name == "routing-policy":
        change_policy("break-vtep", apply)


def sample(kind, probe, origin, stop, rows):
    while not stop.is_set():
        start = time.monotonic()
        value, error = None, ""
        try:
            value = probe()
        except ERRORS as exc:
            error = describe(exc)
        end = time.monotonic()
        rows.append({"probe": kind, "utc": utc(), "start_s": start - origin,
                     "end_s": end - origin, "value": value, "error": error})
        stop.wait(max(0, INTERVAL - (end - start)))


def sustained(rows, condition, start, end=float("inf")):
    matched = []
    for row in rows:
        if row["start_s"] < start or row["end_s"] >= end:
            continue
        if condition(row["value"]):
            matched.append(row["end_s"])
            if len(matched) == REQUIRED:
                return matched[0]
        else:
            matched.clear()
    return None


def counts(rows, start, end):
    values = [row["value"] for row in rows if start <= row["start_s"] < end]
    sent, lost = sum(v is not None for v in values), values.count(False)
    return {"sent": sent, "lost": lost, "errors": values.count(None),
            "loss_pct": round(100 * lost / sent, 2) if sent else None}


def measure(streams, fault, restore, paths):
    def elapsed(when, start):
        return round(when - start, 3) if when is not None else None

    fib = streams["fib"]
    changed = sustained(fib, lambda v: v is not None and len(v) == paths, fault, restore)
    restored = sustained(fib, lambda v: v == BASE_HOPS, restore)
    http_rows = streams["http"]
    first = next((row for row in http_rows if row["start_s"] >= fault and row["value"] is False), None)
    recovered = sustained(http_rows, lambda v: v is True, first["end_s"]) if first else None
    health_observed = any(fault <= row["start_s"] < restore and row["value"] is True for row in http_rows)
    return {
        "fib_convergence_s": elapsed(changed, fault), "fib_restore_s": elapsed(restored, restore),
        "http_state": ("recovered" if recovered is not None else "recovery_unobserved") if first
                      else "no_outage_observed" if health_observed else "unmeasurable",
        "http_first_failure_s": elapsed(first["end_s"], fault) if first else None,
        "http_outage_s": elapsed(recovered, first["end_s"]) if first else None,
        "http_restore_s": elapsed(recovered, restore) if recovered is not None and recovered >= restore else None,
        "icmp_baseline": counts(streams["icmp"], 0, fault),
        "icmp_fault": counts(streams["icmp"], fault, restore),
        "icmp_restore": counts(streams["icmp"], restore, float("inf")),
    }


def observe_fault():
    return {
        "timestamp": utc(), "fib": next_hops(NODE, REMOTE), "http": http(),
        "ipv4": peer_states(NODE, "ipv4"), "evpn": peer_states(NODE, "evpn"),
        "link": ports(NODE)["eth1"]["operstate"],
        "leaf2_ports": {port: state["operstate"] for port, state in ports("leaf2").items()
                        if port in ("eth1", "eth2", "eth3")},
        "leaf2_processes": len(processes("leaf2")),
    }


def matches(name, state):
    hops, healthy = state["fib"], state["http"]
    if len(hops) != FAULTS[name]:
        return False
    neighbors = state["ipv4"]
    established = all(value == "Established" for value in neighbors.values())
    if name == "spine-link":
        return state["link"] != "UP" and neighbors[SPINE1] != "Established" and hops == [SPINE2] and healthy
    if name == "bgp-neighbor":
        return state["link"] == "UP" and neighbors[SPINE1] != "Established" and hops == [SPINE2] and healthy
    if name == "ecmp-path":
        return state["link"] == "UP" and established and healthy
    if name == "leaf-device":
        return state["leaf2_ports"] == dict.fromkeys(("eth1", "eth2", "eth3"), "DOWN") and state["leaf2_processes"] == 0 and not healthy
    return state["link"] == "UP" and established and not healthy


def make_report(folder, result, streams, offsets):
    write_json(folder / "result.json", result)
    (folder / "timeline.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result["events"]))
    with (folder / "samples.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("utc", "probe", "start_s", "end_s", "value", "error"),
                                lineterminator="\n")
        writer.writeheader()
        for row in sorted((row for stream in streams.values() for row in stream), key=lambda r: r["end_s"]):
            writer.writerow({**row, "value": json.dumps(row["value"])})
    logs = folder / "frr"
    logs.mkdir()
    for node, offset in offsets.items():
        source = STATE / node / "frr.log"
        if source.is_file():
            with source.open("rb") as handle:
                handle.seek(offset if source.stat().st_size >= offset else 0)
                (logs / f"{node}.log").write_bytes(handle.read())

    m = result["measurements"]
    loss = m["icmp_fault"]
    def seconds(value):
        return "미관측" if value is None else f"{value:.3f}초"
    lines = [
        f"# 장애 보고서 · {result['scenario']}", "",
        f"- 실행 ID · {result['run']} · {'PASS' if result['pass'] else 'FAIL'}",
        f"- 장애·원복 명령 시작 UTC · {result['fault_at']} / {result['restore_at']}",
        f"- 장애 시 FIB 수렴 · {seconds(m['fib_convergence_s'])}",
        f"- 원복 후 FIB 회복 · {seconds(m['fib_restore_s'])}",
        f"- ICMP 손실 · {loss['lost']}/{loss['sent']} · 수집 오류 {loss['errors']}",
        f"- HTTP · {m['http_state']} · 첫 실패에서 회복까지 {seconds(m['http_outage_s'])}",
        f"- 원복 시작에서 HTTP 회복까지 · {seconds(m['http_restore_s'])}", "",
        "250 ms를 목표로 독립 프로브를 돌렸다. FIB와 HTTP는 연속 세 번 조건을 만족한 첫 샘플을 사용했다.", "",
        "[상태와 시각](result.json) · [샘플](samples.csv) · [작업 이벤트](timeline.jsonl) · [장비 로그](frr/)",
    ]
    lines.extend(f"- 실행 오류 · {error}" for error in result["errors"])
    (folder / "REPORT.md").write_text("\n".join(lines) + "\n")


def exercise(name, observe, recovery, folder):
    baseline = wait_healthy(30)
    if not baseline["pass"]:
        write_json(folder / "precheck-failed.json", baseline)
        raise RuntimeError("Baseline failed before injection.")
    if name == "routing-policy":
        require_free_slot()
    folder.mkdir(parents=True, exist_ok=False)
    offsets = {}
    for node in ROUTERS:
        path = STATE / node / "frr.log"
        offsets[node] = path.stat().st_size if path.is_file() else 0

    origin, stop = time.monotonic(), Event()
    probes = {"fib": lambda: next_hops(NODE, REMOTE), "icmp": lambda: ping("l3"), "http": http}
    streams = {kind: [] for kind in probes}
    workers = [Thread(target=sample, args=(kind, fn, origin, stop, streams[kind]), daemon=True)
               for kind, fn in probes.items()]
    for worker in workers:
        worker.start()
    events, errors = [], []
    fault, restore = float("inf"), float("inf")
    fault_at = restore_at = None
    during, after = {}, {}

    def mark(stage):
        item = event(stage, run=folder.name, scenario=name, elapsed_s=round(time.monotonic() - origin, 6))
        events.append(item)
        return item["timestamp"]

    try:
        end = time.monotonic() + 8
        expected = {"fib": BASE_HOPS, "icmp": True, "http": True}
        while not all(len(streams[key]) >= REQUIRED and all(row["value"] == value for row in streams[key][-REQUIRED:])
                      for key, value in expected.items()):
            if time.monotonic() >= end:
                raise RuntimeError("Baseline did not produce three healthy samples.")
            time.sleep(0.1)
        fault = time.monotonic() - origin
        fault_at = mark("fault_issued")
        apply_fault(name, True)
        mark("fault_applied")
        time.sleep(observe)
        during = observe_fault()
    except (*ERRORS, KeyboardInterrupt) as error:
        errors.append(describe(error) or "interrupted")
    finally:
        if fault_at:
            restore = time.monotonic() - origin
            restore_at = mark("restore_issued")
            try:
                apply_fault(name, False)
                mark("restore_applied")
                after = wait_healthy(recovery)
                time.sleep(1)
                mark("restore_checked")
            except (*ERRORS, KeyboardInterrupt) as error:
                errors.append("restore: " + (describe(error) or "interrupted"))
        stop.set()
        for worker in workers:
            worker.join()
    measurements = measure(streams, fault, restore, FAULTS[name])
    loss = measurements["icmp_fault"]
    passed = (not errors and bool(during) and matches(name, during) and after.get("pass") is True
              and measurements["fib_convergence_s"] is not None and measurements["fib_restore_s"] is not None
              and loss["sent"] > 0 and loss["errors"] == 0
              and measurements["http_state"] in ("recovered", "no_outage_observed")
              and (FAULTS[name] != 0 or measurements["http_restore_s"] is not None))
    result = {"scenario": name, "run": folder.name, "pass": passed, "fault_at": fault_at,
              "restore_at": restore_at, "before": baseline, "during": during, "after": after,
              "events": events, "measurements": measurements, "errors": errors}
    make_report(folder, result, streams, offsets)
    return passed


def interrupt(*_):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=FAULTS)
    parser.add_argument("--observe", type=int, default=12)
    parser.add_argument("--recovery", type=int, default=45)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not 8 <= args.observe <= 120 or not 5 <= args.recovery <= 120:
        parser.error("observe must be 8–120 s and recovery must be 5–120 s")
    folder = args.out or OUT / "drills" / f"{args.scenario}-{uuid4().hex[:8]}"
    signal.signal(signal.SIGTERM, interrupt)
    try:
        with lab_lock():
            require_ready()
            passed = exercise(args.scenario, args.observe, args.recovery, folder)
        print(f"{'PASS' if passed else 'FAIL'} {folder / 'REPORT.md'}")
    except ERRORS as error:
        parser.exit(1, describe(error) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
