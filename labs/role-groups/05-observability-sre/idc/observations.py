"""Journal port and peer transitions across successful IDC scrapes."""
from datetime import datetime, timedelta, timezone
import json

from idc_lab.model import STATE


class Observations:
    def __init__(self, folder=STATE / "observations"):
        self.folder = folder
        self.last = {}

    def record(self, samples):
        now = datetime.now(timezone.utc)
        events = []
        for key, up in samples.items():
            node, kind, subject = key
            if key in self.last and self.last[key] != up:
                field = "interface" if kind == "interface" else "peer"
                events.append({"timestamp": now.isoformat(timespec="milliseconds"), "node": node,
                               "kind": kind + ("_up" if up else "_down"), "source": "exporter", field: subject})
        if events:
            self.folder.mkdir(mode=0o700, exist_ok=True)
            with (self.folder / now.strftime("%Y%m%d%H.jsonl")).open("a", encoding="utf-8") as output:
                output.write("".join(json.dumps(event) + "\n" for event in events))
            cutoff = (now - timedelta(hours=2)).strftime("%Y%m%d%H.jsonl")
            for path in self.folder.glob("*.jsonl"):
                if path.name < cutoff:
                    path.unlink(missing_ok=True)
        self.last.update(samples)
