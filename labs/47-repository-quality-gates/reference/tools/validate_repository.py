from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "validation-summary.md"

REQUIRED_FILES = [
    "README.md",
    "docs/architecture.md",
    "docs/network-design.md",
    "docs/server-setup.md",
    "docs/ansible-automation.md",
    "docs/validation-report.md",
    "docs/team-task-guide.md",
    "docs/pre-run-checklist.md",
    "docs/troubleshooting.md",
    "docs/runbook.md",
    "docs/final-deliverables.md",
    "docs/review-checklist.md",
    "presentation/presentation-outline.md",
    "ansible/ansible.cfg",
    "ansible/inventory.ini",
    "ansible/site.yml",
    "scripts/health_check.sh",
    "scripts/backup.sh",
    "scripts/restore.md",
]

REQUIRED_DIRS = [
    "docs",
    "ansible",
    "scripts",
    "screenshots",
    "screenshots/cloud-infra",
    "screenshots/server",
    "screenshots/ansible",
    "screenshots/validation",
    "presentation",
    "tools",
    ".github/workflows",
]

BLOCKED_SUFFIXES = [
    ".pem",
    ".key",
    ".ppk",
    ".env",
]

BLOCKED_FILENAMES = [
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
]

README_MARKERS = [
    "<!-- AUTO_STATUS_START -->",
    "<!-- AUTO_STATUS_END -->",
]

def check_required_dirs():
    results = []
    for item in REQUIRED_DIRS:
        path = ROOT / item
        ok = path.exists() and path.is_dir()
        results.append((item, ok))
    return results

def check_required_files():
    results = []
    for item in REQUIRED_FILES:
        path = ROOT / item
        ok = path.exists() and path.is_file() and path.stat().st_size > 0
        results.append((item, ok))
    return results

def check_blocked_files():
    blocked = []

    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue

        if path.is_file():
            name = path.name
            suffix = path.suffix

            if suffix in BLOCKED_SUFFIXES:
                blocked.append(str(path.relative_to(ROOT)))

            if name in BLOCKED_FILENAMES:
                blocked.append(str(path.relative_to(ROOT)))

    return blocked

def check_readme_markers():
    readme = ROOT / "README.md"
    if not readme.exists():
        return False

    content = readme.read_text(encoding="utf-8")
    return all(marker in content for marker in README_MARKERS)

def check_tbd_count():
    results = []

    for path in (ROOT / "docs").glob("*.md"):
        content = path.read_text(encoding="utf-8")
        count = content.count("TBD")
        results.append((str(path.relative_to(ROOT)), count))

    return results

def make_icon(ok):
    return "✅" if ok else "❌"

def write_report():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dir_results = check_required_dirs()
    file_results = check_required_files()
    blocked_files = check_blocked_files()
    readme_marker_ok = check_readme_markers()
    tbd_results = check_tbd_count()

    lines = []
    lines.append("# Validation Summary")
    lines.append("")
    lines.append(f"Last Updated: {now}")
    lines.append("")
    lines.append("## 1. Required Directory Check")
    lines.append("")
    lines.append("| Directory | Status |")
    lines.append("|---|---|")

    for item, ok in dir_results:
        lines.append(f"| {item} | {make_icon(ok)} |")

    lines.append("")
    lines.append("## 2. Required File Check")
    lines.append("")
    lines.append("| File | Status |")
    lines.append("|---|---|")

    for item, ok in file_results:
        lines.append(f"| {item} | {make_icon(ok)} |")

    lines.append("")
    lines.append("## 3. README Auto Status Marker Check")
    lines.append("")
    lines.append("| Item | Status |")
    lines.append("|---|---|")
    lines.append(f"| AUTO_STATUS markers | {make_icon(readme_marker_ok)} |")

    lines.append("")
    lines.append("## 4. Sensitive File Check")
    lines.append("")

    if blocked_files:
        lines.append("| Blocked File |")
        lines.append("|---|")
        for item in blocked_files:
            lines.append(f"| {item} |")
    else:
        lines.append("No blocked sensitive files detected.")

    lines.append("")
    lines.append("## 5. TBD Count")
    lines.append("")
    lines.append("| Document | TBD Count |")
    lines.append("|---|---:|")

    for item, count in tbd_results:
        lines.append(f"| {item} | {count} |")

    lines.append("")
    lines.append("## 6. Final Result")
    lines.append("")

    has_missing_dirs = any(not ok for _, ok in dir_results)
    has_missing_files = any(not ok for _, ok in file_results)
    has_blocked_files = len(blocked_files) > 0

    if has_missing_dirs or has_missing_files or has_blocked_files or not readme_marker_ok:
        lines.append("❌ Repository validation found issues.")
    else:
        lines.append("✅ Repository validation passed.")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if has_blocked_files:
        raise SystemExit("Sensitive files detected. Remove them before pushing.")

    if has_missing_dirs or has_missing_files or not readme_marker_ok:
        print("Repository validation found issues. Check docs/validation-summary.md.")
    else:
        print("Repository validation passed.")

if __name__ == "__main__":
    write_report()
