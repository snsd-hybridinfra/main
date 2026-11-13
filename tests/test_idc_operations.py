"""Regression tests for IDC incident correlation and scoped change validation."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ROLES = ROOT / "labs/role-groups"
FABRIC = ROLES / "01-network-fabric/idc"
SRE = ROLES / "05-observability-sre/idc"
for path in (FABRIC, SRE, ROLES / "06-change-automation/idc"):
    sys.path.insert(0, str(path))
incident = importlib.import_module("incident")
validation = importlib.import_module("validation")
observations = importlib.import_module("observations")


def event(second, kind, node="leaf1", source="exporter", **subject):
    return incident.normalize({"timestamp": f"2026-11-13T00:00:{second:02}.000+00:00",
                               "kind": kind, "node": node, "source": source, **subject})


class Incidents(unittest.TestCase):
    def test_fixture_cli_is_deterministic_and_marks_uncertainty(self):
        with TemporaryDirectory() as tmp:
            fixture = SRE / "fixtures/link-incident.json"
            command = [sys.executable, str(ROOT / "tools/idc.py"), "incident", "--input",
                       str(fixture), "--out", tmp]
            subprocess.run(command, check=True, capture_output=True)
            path = Path(tmp) / "incidents.json"
            initial = path.read_bytes()
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(initial, path.read_bytes())
            link, peer = json.loads(initial)["incidents"]
            self.assertEqual((link["link_id"], link["status"], link["cause"]["confidence"]),
                             ("U1", "recovered", "suspected"))
            self.assertEqual([row["run"] for row in link["recent_changes"]], ["demo-description"])
            self.assertEqual(link["recent_changes"][0]["relation"], "temporal_and_scope_only")
            self.assertEqual(len(link["evidence"]), 9)
            self.assertEqual(peer["cause"]["confidence"], "uncertain")
            self.assertIn("추정 원인", (Path(tmp) / "REPORT.md").read_text())

    def test_respects_link_and_time_window(self):
        rows = [event(1, "bgp_down", peer="203.0.113.0"),
                event(12, "interface_down", interface="eth1"),
                event(12, "bgp_down", peer="203.0.113.4")]
        cases = incident.correlate(rows, [], window=10)
        self.assertEqual([case["link_id"] for case in cases], ["U1", "U1", "U3"])
        self.assertTrue(all(case["cause"]["confidence"] == "uncertain" for case in cases))

    def test_duplicate_down_and_new_flap(self):
        rows = [event(1, "bgp_down", peer="203.0.113.0"),
                event(15, "bgp_down", source="loki", peer="203.0.113.0"),
                event(20, "bgp_up", peer="203.0.113.0"),
                event(25, "bgp_down", peer="203.0.113.0")]
        first, second = incident.correlate(reversed(rows), [])
        self.assertEqual((first["status"], len(first["evidence"]), second["status"]),
                         ("recovered", 3, "open"))
        self.assertNotEqual(first["incident_id"], second["incident_id"])

    def test_frr_log_maps_peer_by_device_and_family(self):
        line = "BGP: %ADJCHANGE: neighbor 192.0.2.1(idc-lab) in vrf default Down Hold Timer"
        stamp = "2026-11-13T00:00:01+00:00"
        row = incident.normalize(incident.frr_event("leaf1", stamp, line, "loki"))
        self.assertEqual((row["link_id"], row["family"]), ("U1", "evpn"))
        self.assertIsNone(incident.frr_event("leaf2", stamp, line.replace("192.0.2.1", "192.0.2.11"), "loki"))
        with self.assertRaises(ValueError):
            event(1, "interface_down", interface="outside")

    def test_missing_scrape_is_not_a_down_transition(self):
        with TemporaryDirectory() as tmp:
            journal = observations.Observations(Path(tmp))
            key = ("leaf1", "interface", "eth1")
            journal.record({key: True})
            journal.record({})
            self.assertEqual(list(Path(tmp).glob("*.jsonl")), [])
            journal.record({key: False})
            journal.record({key: False})
            journal.record({key: True})
            rows = list(incident.json_lines(next(Path(tmp).glob("*.jsonl"))))
            self.assertEqual([row["kind"] for row in rows], ["interface_down", "interface_up"])


class Changes(unittest.TestCase):
    def setUp(self):
        self.before = json.loads((FABRIC / "evidence/baseline.json").read_text())
        self.before["interfaces"] = {"leaf1/eth1": "UP"}
        self.config = dict.fromkeys(validation.ROUTERS, "hostname lab\n!\nrouter bgp 65101\n")

    def test_state_drift_is_independent_of_unchanged_bgp_sessions(self):
        after = deepcopy(self.before)
        after["interfaces"]["leaf1/eth1"] = "DOWN"
        after["leaves"]["leaf1"]["next_hops"] = []
        after["probes"]["l3_http"] = False
        checks = {row["check"] for row in validation.compare(self.before, after)}
        self.assertEqual(checks, {"interfaces/leaf1/eth1", "leaves/leaf1/next_hops", "probes/l3_http"})

    def test_transient_kernel_ids_are_ignored(self):
        after = deepcopy(self.before)
        after["leaves"]["leaf1"]["tenant_routes"][0]["nhid"] = 902
        self.assertEqual(validation.compare(self.before, after), [])

    def test_only_the_exact_candidate_is_accepted(self):
        old = self.config["leaf1"]
        new = old.replace("!\n", "!\ninterface eth1\n description IDC-LAB-U1\nexit\n!\n", 1)
        actual = {**self.config, "leaf1": new}
        self.assertTrue(validation.candidate_only("description", self.config, actual))
        self.assertFalse(validation.candidate_only("description", self.config, {**actual, "leaf1": new + "debug bgp\n"}))
        self.assertFalse(validation.candidate_only("description", self.config, {**actual, "leaf2": old + "!\n"}))
        self.assertEqual(validation.commands("break-vtep", False)[0][-1],
                         "no ip prefix-list FABRIC-LOOPBACKS seq 5")

    def test_failed_precheck_blocks_ansible(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "ready").write_text("fabric-1")
            failing = {**self.before, "pass": False, "failures": ["Interface down"]}
            with patch.object(validation, "STATE", directory), \
                 patch.object(validation, "snapshot", return_value=(failing, self.config)), \
                 patch.object(validation, "ansible_change") as ansible:
                result = validation.apply(directory / "blocked", "description")
            self.assertEqual(result["status"], "BLOCKED")
            ansible.assert_not_called()

    def test_recovery_requires_matching_backup_and_runtime(self):
        with TemporaryDirectory(prefix="idc-") as tmp, patch.object(validation, "STATE", Path(tmp)):
            directory = Path(tmp)
            (directory / "ready").write_text("fabric-new")
            (directory / "request.json").write_text(json.dumps({
                "candidate": "description", "run": directory.name, "fabric_id": "fabric-old",
            }))
            with self.assertRaisesRegex(ValueError, "different lab runtime"):
                validation.read_request(directory)
            (directory / "before").mkdir()
            for node, text in self.config.items():
                (directory / "before" / f"{node}.conf").write_text(text)
            before = {"config_sha256": validation.hashes(self.config)}
            self.assertEqual(validation.read_backup(directory, before), self.config)
            (directory / "before/leaf1.conf").write_text("drift")
            with self.assertRaisesRegex(ValueError, "snapshot hashes"):
                validation.read_backup(directory, before)


if __name__ == "__main__":
    unittest.main()
