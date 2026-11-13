"""Collect and correlate link, BGP and change events from the existing IDC lab."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import urlopen

from idc_lab.events import CHANGE_DIR, FRR_LINE, emit
from idc_lab.model import LINKS, OUT, ROUTERS, STATE, address
from idc_lab.runtime import ERRORS, describe, require_ready
from idc_lab.verify import utc, write_json

OBSERVATIONS = STATE / "observations"
LOKI = "http://127.0.0.1:13100"
HISTORY = 300
MAX_INTERVAL = 3600
LOKI_LIMIT = 1000
KINDS = {"interface_down", "interface_up", "bgp_down", "bgp_up"}
CHANGE_KINDS = {"change_issued", "change_applied", "change_checked", "restore_applied"}
CANDIDATES = {"description", "harmless", "break-vtep"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ADJ = re.compile(r"%ADJCHANGE: neighbor ([0-9.]+)(?:\([^)]*\))? in vrf default (Down|Up)\b")
BY_LINK = {link["id"]: link for link in LINKS}
BY_PORT = {tuple(link[side][:2]): link["id"] for link in LINKS for side in ("a", "b")}
BY_PEER = {
    (link[side][0], peer): (link["id"], family)
    for link in LINKS if link["a"][2] and link["b"][2]
    for side, other in (("a", "b"), ("b", "a"))
    for family, peer in (("ipv4", address(link[other][2])), ("evpn", ROUTERS[link[other][0]]["loopback"]))
}


def parse_time(value):
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError("Timestamp requires a UTC offset.")
    return stamp.astimezone(timezone.utc)


def timestamp(stamp):
    return stamp.isoformat(timespec="milliseconds")


def stable_id(prefix, *parts):
    return prefix + sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()[:20]


def normalize(item):
    node, kind, source = (item[key] for key in ("node", "kind", "source"))
    if node not in ROUTERS or kind not in KINDS:
        raise ValueError("Unknown event node or kind.")
    stamp = timestamp(parse_time(item["timestamp"]))
    if kind.startswith("interface_"):
        subject = item["interface"]
        link = BY_PORT.get((node, subject))
        detail = {"interface": subject}
        source_valid = source == "exporter"
    else:
        subject = item["peer"]
        link, family = BY_PEER.get((node, subject), (None, None))
        detail = {"peer": subject, "family": family}
        source_valid = source in ("exporter", "frr_file", "loki")
    if not link or not source_valid:
        raise ValueError("Event does not match a lab port, peer or source.")
    return {"event_id": stable_id("evt-", stamp, kind, node, subject, source), "timestamp": stamp,
            "kind": kind, "node": node, "link_id": link, "source": source, **detail}


def frr_event(node, stamp, line, source):
    match = ADJ.search(line)
    if match and (node, match[1]) in BY_PEER:
        return {"timestamp": stamp, "kind": "bgp_" + match[2].lower(),
                "node": node, "source": source, "peer": match[1]}
    return None


def json_lines(path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.endswith("\n") and line.strip():
                yield json.loads(line)


def local_syslog(since):
    for node in ROUTERS:
        path = STATE / node / "frr.log"
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if match := FRR_LINE.match(line):
                        stamp = parse_time(match[1].replace("/", "-") + "+00:00")
                        if stamp >= since and (item := frr_event(node, timestamp(stamp), match[2], "frr_file")):
                            yield item
        except FileNotFoundError:
            continue


def loki_rows(app, since, until):
    params = urlencode({
        "query": '{job="idc-syslog",app="' + app + '"}',
        "start": str(int(since.timestamp() * 1_000_000_000)),
        "end": str(int(until.timestamp() * 1_000_000_000)),
        "limit": LOKI_LIMIT, "direction": "forward",
    })
    with urlopen(LOKI + "/loki/api/v1/query_range?" + params, timeout=8) as response:
        data = json.load(response)
    if data["status"] != "success" or data["data"]["resultType"] != "streams":
        raise ValueError("Unexpected Loki result.")
    rows = [(stream["stream"]["node"], timestamp(datetime.fromtimestamp(int(stamp) / 1e9, timezone.utc)), line)
            for stream in data["data"]["result"] for stamp, line in stream["values"]]
    if len(rows) >= LOKI_LIMIT:
        raise ValueError("Loki reached the query limit. Select a shorter interval.")
    return rows


def normalize_change(raw):
    node, event, run, candidate = (raw.get(k) for k in ("node", "event", "run", "candidate"))
    if (node not in ROUTERS or event not in CHANGE_KINDS or candidate not in CANDIDATES
            or not isinstance(run, str) or not SLUG.fullmatch(run)):
        return None
    port = raw.get("interface")
    if port is not None and (node, port) not in BY_PORT:
        raise ValueError("Change scope does not match a lab port.")
    return {"timestamp": timestamp(parse_time(raw["timestamp"])), "event": event, "run": run,
            "node": node, "candidate": candidate, "interface": port}


def collect(since, until, loki):
    rows = []
    for path in sorted(OBSERVATIONS.glob("*.jsonl")):
        try:
            rows.extend(json_lines(path))
        except FileNotFoundError:
            continue
    changes = [json.loads(path.read_text()) for path in sorted(CHANGE_DIR.glob("*.json"))]
    rows.extend(local_syslog(since))
    if loki:
        for node, stamp, line in loki_rows("frr", since, until):
            if item := frr_event(node, stamp, line, "loki"):
                rows.append(item)
        # The local journal is authoritative for this lab runtime; older Loki runs stay visible in Grafana.
    return rows, changes


def subject_key(row):
    return row["node"], row["kind"].split("_")[0], row.get("interface") or row["peer"]


def episodes(rows, window):
    active, latest = {}, None
    groups = []
    for row in sorted(rows, key=lambda r: (r["timestamp"], r["kind"].endswith("_up"), r["event_id"])):
        key = subject_key(row)
        if row["kind"].endswith("_up"):
            if group := active.pop(key, None):
                group["evidence"].append(row)
                group["down"].remove(key)
                if not group["down"]:
                    group["recovered_at"] = row["timestamp"]
            continue
        group = active.get(key)
        if group is None:
            stamp = parse_time(row["timestamp"])
            if latest is None or not latest["down"] or (stamp - latest["started"]).total_seconds() > window:
                latest = {"started": stamp, "down": set(), "recovered_at": None, "evidence": []}
                groups.append(latest)
            group = latest
            active[key] = group
            group["down"].add(key)
        group["evidence"].append(row)
    return groups


def recent_changes(changes, endpoints, started):
    ports = {(item["node"], item["interface"]) for item in endpoints}
    nodes = {node for node, _ in ports}
    relevant = {}
    for item in sorted(changes, key=lambda r: (r["timestamp"], r["run"], r["event"])):
        seconds = (started - parse_time(item["timestamp"])).total_seconds()
        if not 0 <= seconds <= HISTORY or item["node"] not in nodes:
            continue
        if item["interface"] is not None and (item["node"], item["interface"]) not in ports:
            continue
        relevant[item["run"]] = {**item, "seconds_before": round(seconds, 3),
                                 "relation": "temporal_and_scope_only"}
    return list(relevant.values())


def correlate(events, changes, window=10):
    by_link = defaultdict(dict)
    for row in events:
        by_link[row["link_id"]][row["event_id"]] = row
    incidents = []
    for link, rows in by_link.items():
        endpoints = [{"node": BY_LINK[link][side][0], "interface": BY_LINK[link][side][1]}
                     for side in ("a", "b")]
        for group in episodes(rows.values(), window):
            start, recovery, evidence = group["started"], group["recovered_at"], group["evidence"]
            downs = [row for row in evidence if row["kind"].endswith("_down") and
                     (parse_time(row["timestamp"]) - start).total_seconds() <= window]
            port_down = [row for row in downs if row["kind"] == "interface_down"]
            peer_down = [row for row in downs if row["kind"] == "bgp_down" and row["family"] == "ipv4"]
            suspected = bool(port_down and peer_down)
            incidents.append({
                "incident_id": stable_id("inc-", link, timestamp(start)),
                "link_id": link, "started_at": timestamp(start), "recovered_at": recovery,
                "status": "recovered" if recovery else "open",
                "nodes": sorted({p["node"] for p in endpoints}), "endpoints": endpoints, "evidence": evidence,
                "cause": {"kind": "link_failure_suspected" if suspected else "undetermined",
                          "confidence": "suspected" if suspected else "uncertain",
                          "basis": sorted(row["event_id"] for row in ((*port_down, *peer_down) if suspected else downs))},
                "recent_changes": recent_changes(changes, endpoints, start),
            })
    return sorted(incidents, key=lambda row: (row["started_at"], row["link_id"]))


def write_report(folder, result):
    write_json(folder / "incidents.json", result)
    lines = ["# 네트워크 장애 상관분석", "", f"UTC {result['from']} ~ {result['to']} · {result['source']}",
             f"사건 {len(result['incidents'])}건 · 결합 창 {result['correlation_window_s']}초", ""]
    for item in result["incidents"]:
        endpoints = " ↔ ".join(f"{p['node']}/{p['interface']}" for p in item["endpoints"])
        cause = "링크 장애 의심" if item["cause"]["confidence"] == "suspected" else "불확실"
        lines += [f"## {item['link_id']} · {item['incident_id']}", "",
                  f"- 연결 · {endpoints}", f"- 최초 관측 · {item['started_at']}",
                  f"- 복구 · {item['recovered_at'] or '미관측'}", f"- 추정 원인 · {cause}", ""]
        for row in item["evidence"]:
            subject = row.get("interface") or row.get("peer")
            lines.append(f"- {row['timestamp']} · {row['node']} {subject} · {row['kind']} · {row['source']}")
        if item["recent_changes"]:
            lines += ["", "관련 범위의 최근 변경", ""]
            for change in item["recent_changes"]:
                lines.append(f"- {change['run']} · {change['candidate']} · {change['seconds_before']}초 전")
            lines += ["", "변경과 장애의 인과관계는 추가 확인이 필요합니다."]
        lines.append("")
    lines.append("[사건 및 근거 JSON](incidents.json)")
    (folder / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def publish(incidents):
    for item in incidents:
        row = {key: item[key] for key in ("incident_id", "link_id", "started_at", "status")}
        row["cause"] = item["cause"]["kind"]
        row["changes"] = ",".join(change["run"] for change in item["recent_changes"])
        emit("idc-lab", "incident", json.dumps(row))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=Path, help="Synthetic fixture")
    mode.add_argument("--since", help="Live query start with UTC offset")
    parser.add_argument("--until", help="Live query end, defaults to now")
    parser.add_argument("--loki", action="store_true", help="Read existing local Loki Syslog")
    parser.add_argument("--publish", action="store_true", help="Publish cases through local Syslog")
    parser.add_argument("--window", type=int, default=10)
    parser.add_argument("--out", type=Path, default=OUT / "operations/incidents")
    args = parser.parse_args()
    if not 1 <= args.window <= 60 or (args.input and (args.until or args.loki or args.publish)):
        parser.error("Use a 1–60 s window. --until, --loki and --publish apply to live queries.")
    try:
        if args.input:
            fixture = json.loads(args.input.read_text())
            since, until = (parse_time(fixture[key]) for key in ("from", "to"))
            source = "synthetic-fixture"
        else:
            require_ready()
            since, until = parse_time(args.since), parse_time(args.until or utc())
            source = "live-exporter-and-frr" + ("-loki" if args.loki else "")
        if not 0 < (until - since).total_seconds() <= MAX_INTERVAL:
            raise ValueError("The query interval must be positive and at most one hour.")
        rows, raw_changes = ((fixture["events"], fixture["changes"]) if args.input
                             else collect(since, until, args.loki))
        events = [normalize(row) for row in rows if since <= parse_time(row["timestamp"]) <= until]
        changes = [item for row in raw_changes if (item := normalize_change(row)) is not None]
        incidents = correlate(events, changes, args.window)
        result = {"schema_version": 1, "source": source, "from": timestamp(since), "to": timestamp(until),
                  "correlation_window_s": args.window, "recent_change_window_s": HISTORY, "incidents": incidents}
        write_report(args.out, result)
        if args.publish:
            publish(incidents)
    except (*ERRORS, KeyError, TypeError) as error:
        parser.exit(1, describe(error) + "\n")
    print(f"{len(incidents)} incident(s) · {args.out / 'REPORT.md'}")


if __name__ == "__main__":
    main()
