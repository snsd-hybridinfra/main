"""Evaluate a lab policy change and prove the inverse restores configuration and service."""
import argparse
from difflib import unified_diff
from pathlib import Path
import signal
import time
from uuid import uuid4

from idc_lab.events import event
from idc_lab.model import OUT
from idc_lab.policy import CANDIDATES, NODE, change_policy, require_free_slot, running
from idc_lab.runtime import ERRORS, describe, lab_lock, require_ready
from idc_lab.verify import wait_healthy, write_json


def exercise(candidate, folder):
    baseline = wait_healthy(25)
    if not baseline["pass"]:
        write_json(folder / "precheck-failed.json", baseline)
        raise RuntimeError("Baseline failed before the change.")
    require_free_slot()
    before = running()
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "before.conf").write_text(before)
    applied, restored, restored_text = {}, {}, ""
    errors = []
    events = [event("change_issued", run=folder.name, node=NODE, candidate=candidate)]
    try:
        change_policy(candidate, True)
        applied_text = running()
        (folder / "applied.conf").write_text(applied_text)
        if applied_text == before:
            raise RuntimeError("The candidate did not change the running configuration.")
        delta = unified_diff(before.splitlines(keepends=True), applied_text.splitlines(keepends=True),
                             fromfile="before.conf", tofile="applied.conf")
        (folder / "change.diff").write_text("".join(delta))
        time.sleep(1)  # Give the asynchronous inbound refresh time to update the kernel FIB.
        applied = wait_healthy(8)
        events.append(event("change_checked", run=folder.name, passed=applied["pass"]))
    except (*ERRORS, KeyboardInterrupt) as error:
        errors.append(describe(error) or "interrupted")
    finally:
        events.append(event("rollback_issued", run=folder.name, node=NODE))
        try:
            change_policy(candidate, False)
            restored = wait_healthy(45)
            restored_text = running()
            (folder / "restored.conf").write_text(restored_text)
            events.append(event("rollback_checked", run=folder.name, passed=restored["pass"]))
        except (*ERRORS, KeyboardInterrupt) as error:
            errors.append("rollback: " + (describe(error) or "interrupted"))
    identical = restored_text == before
    restored_ok = restored.get("pass") is True and identical
    if not restored_ok:
        status = "ROLLBACK_FAILED"
    elif errors or "pass" not in applied:
        status = "ERROR_ROLLED_BACK"
    elif applied["pass"]:
        status = "VERIFIED_ROLLED_BACK"
    else:
        status = "REJECTED_ROLLED_BACK"
    failed_as_expected = (applied.get("probes", {}).get("l3_http") is False
                          and (applied.get("leaves", {}).get(NODE) or {}).get("next_hops") == [])
    passed = (status == "VERIFIED_ROLLED_BACK" if candidate == "harmless"
              else status == "REJECTED_ROLLED_BACK" and failed_as_expected)
    summary = {"candidate": candidate, "status": status, "pass": passed, "config_restored": identical,
               "baseline": baseline, "applied": applied, "restored": restored, "events": events, "errors": errors}
    write_json(folder / "result.json", summary)
    return summary


def interrupt(*_):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", choices=CANDIDATES)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    folder = args.out or OUT / "changes" / f"{args.candidate}-{uuid4().hex[:8]}"
    signal.signal(signal.SIGTERM, interrupt)
    try:
        with lab_lock():
            require_ready()
            result = exercise(args.candidate, folder)
        print(f"{result['status']} · {folder / 'result.json'}")
    except ERRORS as error:
        parser.exit(1, describe(error) + "\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
