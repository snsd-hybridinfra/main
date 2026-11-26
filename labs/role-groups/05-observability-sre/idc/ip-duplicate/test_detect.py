"""Regression tests for the read-only IP duplicate detection proof of concept."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from detect import detect, normalize_claim, syslog

FIXTURE = json.loads((Path(__file__).parent / "fixtures/synthetic.json").read_text(encoding="utf-8"))


class DetectorTests(unittest.TestCase):
    def test_fixture_two_alerts(self):
        alerts = detect(FIXTURE)
        self.assertEqual(len(alerts), 2)
        self.assertEqual({a["event"] for a in alerts},
                         {"IP_DUPLICATE_SUSPECTED", "GATEWAY_IP_UNEXPECTED_MAC"})
        self.assertEqual({a["ip"] for a in alerts}, {"192.0.2.1", "192.0.2.10"})
        self.assertEqual({a["severity"] for a in alerts}, {"critical", "warning"})

    def test_same_mac_from_different_switches_no_alert(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.20"]
        self.assertEqual(detect(data), [])

    def test_stale_mac_change_no_alert(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.30"]
        self.assertEqual(detect(data), [])

    def test_different_segments_do_not_collide(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.10" and o["mac"] != "02:00:00:00:00:0b"]
        self.assertEqual(detect(data), [])

    def test_gateway_allowed_identity_is_normal(self):
        data = deepcopy(FIXTURE)
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.1" and o["mac"] == "02:00:00:00:ff:01"]
        self.assertEqual(detect(data), [])

    def test_unexpected_gateway_mac_even_if_one_claim(self):
        data = deepcopy(FIXTURE)
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.1" and o["mac"] == "02:00:00:00:ff:fe"]
        alerts = detect(data)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["status"], "suspected")

    def test_fdb_event_not_arp_evidence(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        data["observations"] = [{**o, "type": "mac_fdb"} for o in data["observations"]]
        self.assertEqual(detect(data), [])

    def test_reject_invalid_ip_mac_and_timestamp(self):
        claim = FIXTURE["observations"][0]
        for name, value in (("ip", "not-ip"), ("mac", "00:bad"), ("timestamp", "2026-11-13T06:00:00")):
            with self.subTest(field=name), self.assertRaises(ValueError):
                normalize_claim({**claim, name: value})

    def test_syslog_preview_is_local_only(self):
        lines = [syslog(item) for item in detect(FIXTURE)]
        self.assertTrue(any(line.startswith("<130>1 ") for line in lines))
        self.assertTrue(any(line.startswith("<132>1 ") for line in lines))
        self.assertTrue(all("ipdup-lab arp-detector" in line for line in lines))

    def test_window_must_be_positive(self):
        with self.assertRaises(ValueError):
            detect(FIXTURE, 0)

    def test_planned_gateway_mac_change_allowlist(self):
        # Both MACs must be explicitly authorized for a planned transition.
        data = deepcopy(FIXTURE)
        data["gateway_baselines"][0]["allowed_macs"].append("02:00:00:00:ff:fe")
        data["observations"] = [o for o in data["observations"] if o["ip"] == "192.0.2.1"]
        self.assertEqual(detect(data), [])

    def test_unknown_mac_still_alerts_during_gateway_transition(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"][0]["allowed_macs"].append("02:00:00:00:ff:fe")
        observations = [o for o in data["observations"] if o["ip"] == "192.0.2.1"]
        observations.append({**observations[-1], "timestamp": "2026-11-13T06:00:30Z",
                             "mac": "02:00:00:00:ff:99"})
        data["observations"] = observations
        alerts = detect(data)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["event"], "GATEWAY_IP_UNEXPECTED_MAC")
        self.assertIn("02:00:00:00:ff:99", alerts[0]["macs"])

    def test_repeated_sensor_observations_do_not_duplicate_incident(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        # The fixture also uses .10 in another L2 segment; select one domain.
        samples = [o for o in data["observations"]
                   if o["ip"] == "192.0.2.10" and o["segment"] == "BD100-VNI10100"]
        data["observations"] = samples + [
            {**samples[-1], "timestamp": "2026-11-13T06:00:40Z", "device": "leaf-third"}
        ]
        alerts = detect(data)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["sources"], ["leaf-arista", "leaf-cisco", "leaf-third"])

    def test_separated_duplicate_ip_episodes_are_not_merged(self):
        data = deepcopy(FIXTURE)
        data["gateway_baselines"] = []
        samples = [o for o in data["observations"] if o["ip"] == "192.0.2.10"]
        data["observations"] = [
            {**samples[0], "timestamp": "2026-11-13T06:00:00Z"},
            {**samples[1], "timestamp": "2026-11-13T06:00:10Z"},
            {**samples[0], "timestamp": "2026-11-13T06:10:00Z"},
            {**samples[1], "timestamp": "2026-11-13T06:10:10Z"},
        ]
        alerts = detect(data)
        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["first_seen"], "2026-11-13T06:00:00+00:00")
        self.assertEqual(alerts[0]["last_seen"], "2026-11-13T06:00:10+00:00")
        self.assertEqual(alerts[1]["first_seen"], "2026-11-13T06:10:00+00:00")
        self.assertEqual(alerts[1]["last_seen"], "2026-11-13T06:10:10+00:00")


if __name__ == "__main__":
    unittest.main()
