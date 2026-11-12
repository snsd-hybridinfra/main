"""Check one-to-one ownership of the portfolio's numbered labs."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
GROUP_ROOT = "labs/role-groups"


def check_catalog(root):
    manifest = json.loads((root / GROUP_ROOT / "manifest.json").read_text())
    canonical = {}
    for path in sorted((root / "labs").iterdir()):
        match = re.fullmatch(r"(\d{2})-[a-z0-9-]+", path.name)
        if not match or not path.is_dir():
            continue
        lab_id = int(match[1])
        if lab_id in canonical:
            raise ValueError(f"Duplicate lab ID on disk: {lab_id}")
        if not (path / "README.md").is_file():
            raise ValueError(f"Missing README: {path.name}")
        canonical[lab_id] = path.relative_to(root).as_posix()

    owners = {}
    groups = set()
    for group in manifest["groups"]:
        name = group["id"]
        if not re.fullmatch(r"\d{2}-[a-z0-9-]+", name) or name in groups:
            raise ValueError(f"Invalid or duplicate role group: {name}")
        groups.add(name)
        index = (root / GROUP_ROOT / name / "README.md").read_text()
        if group["primary_ids"] != [lab["id"] for lab in group["labs"]]:
            raise ValueError(f"{name}: primary IDs and lab entries differ")
        for lab in group["labs"]:
            lab_id, path = lab["id"], lab["path"]
            if lab_id in owners or canonical.get(lab_id) != path:
                raise ValueError(f"{name}: duplicate or invalid lab {lab_id} ({path})")
            link = "../../" + Path(path).name + "/README.md"
            if f"]({link})" not in index:
                raise ValueError(f"{name}: missing canonical link for lab {lab_id}")
            owners[lab_id] = name

    if owners.keys() != canonical.keys() or manifest["lab_count"] != len(canonical):
        raise ValueError("Canonical labs and role ownership are inconsistent")
    if manifest["group_count"] != len(groups):
        raise ValueError("Group count differs from the manifest")
    return {"labs": len(canonical), "groups": len(groups), "unique_assignments": len(owners)}


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
