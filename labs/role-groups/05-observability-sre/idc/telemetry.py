"""Expose the fabric to Prometheus, Alloy and Alertmanager."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from threading import Event, Lock, Thread

from idc_lab.events import emit
from idc_lab.model import LEAVES, OUT, ROUTERS, STATE, interfaces
from idc_lab.runtime import ERRORS, describe, require_ready
from idc_lab.verify import http, next_hops, peer_states, ports, utc

METRICS = {
    "idc_link_oper_up": ("gauge", "Physical lab interface operational state."),
    "idc_interface_rx_bytes_total": ("counter", "Received bytes."),
    "idc_interface_tx_bytes_total": ("counter", "Transmitted bytes."),
    "idc_bgp_peer_up": ("gauge", "Expected BGP peer is Established."),
    "idc_ecmp_nexthops": ("gauge", "Installed next hops to the remote VTEP."),
    "idc_service_probe_success": ("gauge", "Synthetic HTTP probe returned expected payload."),
    "idc_query_success": ("gauge", "Collection query completed."),
}
TIMESTAMP = re.compile(r"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d(?:\.\d+)?) (.+)")


def sample(name, value, **labels):
    tags = ",".join(f"{key}={json.dumps(str(val))}" for key, val in labels.items())
    return name, f"{name}{{{tags}}} {int(value)}"


def collect(node, query, fn):
    try:
        rows = fn()
        return [*rows, sample("idc_query_success", 1, node=node, query=query)]
    except ERRORS:
        return [sample("idc_query_success", 0, node=node, query=query)]


def interface_metrics(node):
    rows = ports(node)
    for port, *_ in interfaces(node):
        state = rows.get(port, {})
        yield sample("idc_link_oper_up", state.get("operstate") == "UP", node=node, interface=port)
        stats = state.get("stats64") or state.get("stats") or {}
        for direction in ("rx", "tx"):
            if "bytes" in stats.get(direction, {}):
                yield sample(f"idc_interface_{direction}_bytes_total", stats[direction]["bytes"],
                             node=node, interface=port)


def router_metrics(node):
    rows = collect(node, "interfaces", lambda: interface_metrics(node))
    for family in ("ipv4", "evpn"):
        rows += collect(node, family, lambda: [
            sample("idc_bgp_peer_up", state == "Established", node=node, afi=family, peer=peer)
            for peer, state in peer_states(node, family).items()])
    if node in LEAVES:
        remote = next(ROUTERS[other]["loopback"] for other in LEAVES if other != node)
        rows += collect(node, "fib", lambda: [
            sample("idc_ecmp_nexthops", len(next_hops(node, remote + "/32")), node=node, remote=remote)])
    return rows


def service_metrics(path):
    return collect("host1", f"http-{path}", lambda: [sample("idc_service_probe_success", http(path), path=path)])


def metrics_body():
    series = {metric: [] for metric in METRICS}
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [pool.submit(router_metrics, node) for node in ROUTERS]
        jobs += [pool.submit(service_metrics, path) for path in ("l2", "l3")]
        for job in jobs:
            for metric, row in job.result():
                series[metric].append(row)
    lines = []
    for metric, (kind, description) in METRICS.items():
        lines += [f"# HELP {metric} {description}", f"# TYPE {metric} {kind}", *series[metric]]
    return ("\n".join(lines) + "\n").encode()


def relay(stop):
    positions = {}
    while not stop.is_set():
        for node in ROUTERS:
            source = STATE / node / "frr.log"
            try:
                with source.open("rb") as handle:
                    stat = source.stat()
                    inode, offset = positions.get(node, (None, 0))
                    handle.seek(offset if inode == stat.st_ino and offset <= stat.st_size else 0)
                    while raw := handle.readline():
                        if not raw.endswith(b"\n"):
                            break
                        message = raw.decode(errors="replace").strip()
                        stamp = None
                        if parsed := TIMESTAMP.match(message):
                            stamp = datetime.fromisoformat(parsed[1].replace("/", "-")).replace(
                                tzinfo=timezone.utc).isoformat(timespec="milliseconds")
                            message = parsed[2]
                        if message:
                            emit(node, "frr", message[:3000], stamp)
                        positions[node] = stat.st_ino, handle.tell()
            except OSError:
                continue
        stop.wait(0.5)


class Handler(BaseHTTPRequestHandler):
    def respond(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/metrics":
            self.respond(metrics_body(), "text/plain; version=0.0.4; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/alerts":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 1 <= length <= 1_000_000:
                raise ValueError("Invalid webhook length")
            alerts = json.loads(self.rfile.read(length))["alerts"]
            records = [
                {"timestamp": utc(), "event": "alert", "status": item["status"],
                 "alert": item["labels"]["alertname"],
                 **{key: item["labels"].get(key) for key in ("node", "interface", "peer", "path")}}
                for item in alerts
            ]
        except (KeyError, TypeError, ValueError, AttributeError):
            self.send_error(400)
            return
        with self.server.alert_lock, self.server.alert_file.open("a") as output:
            for item in records:
                line = json.dumps(item)
                output.write(line + "\n")
                emit("idc-lab", "alertmanager", line, item["timestamp"])
        self.respond(b"ok\n", "text/plain")

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alerts-file", type=Path, default=OUT / "alerts.jsonl")
    args = parser.parse_args()
    try:
        require_ready()
        args.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        with ThreadingHTTPServer(("127.0.0.1", 19808), Handler) as server:
            server.alert_lock, server.alert_file = Lock(), args.alerts_file
            stop = Event()
            watcher = Thread(target=relay, args=(stop,), daemon=True)
            watcher.start()
            print("IDC metrics and alert webhook listening on 127.0.0.1:19808", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                stop.set()
                watcher.join()
    except ERRORS as error:
        parser.exit(1, describe(error) + "\n")


if __name__ == "__main__":
    main()
