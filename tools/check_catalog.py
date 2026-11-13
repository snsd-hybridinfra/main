"""Check that every experiment belongs to one operating lab."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
GROUP_ROOT = "labs/role-groups"


def check_catalog(root):
    manifest = json.loads((root / GROUP_ROOT / "manifest.json").read_text())
    if manifest["schema_version"] != "2.0":
        raise ValueError("Unsupported catalog schema")
    group_root = root / GROUP_ROOT
    portfolio = (root / "README.md").read_text()
    directories = {p.name for p in group_root.iterdir() if p.is_dir() and re.fullmatch(r"\d{2}-[a-z0-9-]+", p.name)}
    if any(p.is_dir() and re.match(r"\d{2}-", p.name) for p in (root / "labs").iterdir()):
        raise ValueError("Legacy experiment directories must be inside their operating lab")

    groups = set()
    experiments = set()
    for lab in manifest["labs"]:
        name = lab["id"]
        if name in groups or name not in directories:
            raise ValueError(f"Duplicate or missing lab: {name}")
        groups.add(name)
        if f"]({GROUP_ROOT}/{name}/README.md)" not in portfolio:
            raise ValueError(f"Missing portfolio link: {name}")
        folder = group_root / name
        index = (folder / "README.md").read_text()
        on_disk = {p for p in (folder / "experiments").iterdir() if p.is_dir()}
        listed = set()
        for experiment in lab["experiments"]:
            path = root / experiment["path"]
            if path not in on_disk or path in experiments:
                raise ValueError(f"Invalid or duplicate experiment: {path}")
            link = (path.relative_to(folder) / "README.md").as_posix()
            if not (folder / link).is_file() or f"]({link})" not in index:
                raise ValueError(f"Missing experiment README or link: {path}")
            if experiment["status"] not in {"PREVIOUS_LOCAL_EVIDENCE", "SOURCE_EXTRACTED_NOT_REVALIDATED"}:
                raise ValueError(f"Unknown evidence status: {path}")
            listed.add(path)
            experiments.add(path)
        if listed != on_disk:
            raise ValueError(f"Unlisted experiments in {name}")

    if groups != directories or len(groups) != manifest["lab_count"]:
        raise ValueError("Lab directories and catalog differ")
    if len(experiments) != manifest["experiment_count"]:
        raise ValueError("Experiment count differs from the catalog")
    return {"labs": len(groups), "experiments": len(experiments)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        summary = check_catalog(args.root)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
