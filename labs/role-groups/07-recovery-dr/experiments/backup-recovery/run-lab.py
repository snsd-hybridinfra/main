#!/usr/bin/env python3
"""Measure restore time, data loss, and endpoint failover for a synthetic service."""
from __future__ import annotations

import argparse
import json
from contextlib import closing
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

SERVICE = Path(__file__).with_name("service.py")


def utc():
    return datetime.now(timezone.utc)


def request(port, path, value=None):
    body = None if value is None else json.dumps({"value": value}).encode()
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method="POST" if body else "GET",
    )
    with urlopen(req, timeout=1) as response:
        return json.load(response)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start(db, port):
    process = subprocess.Popen(
        [sys.executable, str(SERVICE), "--db", str(db), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("service exited before health check")
        try:
            if request(port, "/health")["ok"]:
                return process
        except (URLError, TimeoutError, HTTPException):
            time.sleep(0.05)
    process.terminate()
    process.wait(timeout=3)
    raise TimeoutError("service did not start within five seconds")


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def endpoint_down(port):
    try:
        request(port, "/health")
    except (URLError, TimeoutError, HTTPException):
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="lab05-recovery-") as work:
        root = Path(work)
        primary_site = root / "site-a"
        recovery_site = root / "site-b"
        backup_store = root / "isolated-backup"
        primary_site.mkdir()
        recovery_site.mkdir()
        backup_store.mkdir()
        primary_db = primary_site / "service.sqlite3"
        recovery_db = recovery_site / "service.sqlite3"
        backup = backup_store / "snapshot.sqlite3"
        primary_port = free_port()
        recovery_port = free_port()
        while recovery_port == primary_port:
            recovery_port = free_port()
        primary_process = None
        recovery_process = None
        try:
            primary_process = start(primary_db, primary_port)
            for n in range(1, 4):
                assert request(primary_port, "/events", f"baseline-{n}")["seq"] == n
            before = request(primary_port, "/health")
            with closing(sqlite3.connect(primary_db)) as source, closing(sqlite3.connect(backup)) as target:
                source.backup(target)
            backup_at = utc()
            for n in range(4, 6):
                assert request(primary_port, "/events", f"after-backup-{n}")["seq"] == n
            pre_failure = request(primary_port, "/health")
            failure_at = utc()
            failure_start = time.monotonic()
            stop(primary_process)
            primary_process = None
            primary_db.unlink()
            outage_confirmed = endpoint_down(primary_port)
            if not outage_confirmed:
                raise AssertionError("primary-site outage was not observed")
            bad_restore_rejected = False
            try:
                shutil.copyfile(backup_store / "missing-snapshot.sqlite3", recovery_db)
            except FileNotFoundError:
                bad_restore_rejected = True
            shutil.copyfile(backup, recovery_db)
            recovery_process = start(recovery_db, recovery_port)
            after = request(recovery_port, "/health")
            rto_seconds = round(time.monotonic() - failure_start, 3)
            primary_endpoint_still_down = endpoint_down(primary_port)
            lost_events = pre_failure["count"] - after["count"]
            isolated_paths = (
                primary_site != recovery_site
                and backup.parent not in (primary_site, recovery_site)
            )
            if not (
                before["count"] == 3
                and pre_failure["count"] == 5
                and after["count"] == 3
                and after["last_seq"] == 3
                and lost_events == 2
                and outage_confirmed
                and bad_restore_rejected
                and primary_endpoint_still_down
                and isolated_paths
            ):
                raise AssertionError("unexpected backup or site-recovery result")
            result = {
                "status": "pass",
                "at_utc": utc().isoformat(),
                "baseline_events": before["count"],
                "events_before_failure": pre_failure["count"],
                "events_after_restore": after["count"],
                "lost_events": lost_events,
                "backup_to_failure_seconds": round((failure_at - backup_at).total_seconds(), 3),
                "site_recovery_rto_seconds": rto_seconds,
                "primary_outage_observed": outage_confirmed,
                "primary_endpoint_still_down": primary_endpoint_still_down,
                "recovery_endpoint_healthy": after["ok"],
                "endpoint_changed": primary_port != recovery_port,
                "missing_backup_rejected": bad_restore_rejected,
                "isolated_local_paths": isolated_paths,
                "storage": "temporary local directories and SQLite; deleted after run",
                "scope": "local site model only; no cloud region, physical data center, replication, or traffic manager",
            }
            rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if args.evidence:
                Path(args.evidence).write_text(rendered, encoding="utf-8", newline="\n")
            print(rendered, end="")
        finally:
            stop(primary_process)
            stop(recovery_process)


if __name__ == "__main__":
    main()
