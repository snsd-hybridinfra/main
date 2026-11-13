#!/usr/bin/env python3
"""Create a deterministic SHA-256 fingerprint for one RV execution record."""
import argparse,json
from pathlib import Path
from rv_common import execution_fingerprint,load
def main()->int:
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("record",type=Path); a=p.parse_args(); value=load(a.record); print(execution_fingerprint(value)); return 0
if __name__=="__main__": raise SystemExit(main())
