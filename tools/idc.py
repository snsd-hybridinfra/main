"""Run a stage of the IDC scenario from the portfolio root."""
import argparse
from pathlib import Path
import runpy
import sys

ROLES = Path(__file__).resolve().parent.parent / "labs/role-groups"
FABRIC = ROLES / "01-network-fabric/idc"
MODULES = {"render": "render", "fabric": "runtime", "verify": "verify", "inventory": "inventory"}
SCRIPTS = {
    "observe": ROLES / "05-observability-sre/idc/telemetry.py",
    "change": ROLES / "06-change-automation/idc/change.py",
    "drill": ROLES / "07-recovery-dr/idc/drill.py",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=(*MODULES, *SCRIPTS))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    sys.path.insert(0, str(FABRIC))
    sys.argv = [f"idc.py {args.stage}", *args.args]
    if args.stage in MODULES:
        runpy.run_module(f"idc_lab.{MODULES[args.stage]}", run_name="__main__")
    else:
        runpy.run_path(str(SCRIPTS[args.stage]), run_name="__main__")


if __name__ == "__main__":
    main()
