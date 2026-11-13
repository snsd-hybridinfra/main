from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IMAGE_SECTIONS = {
    "docs/network-design.md": [
        ("Cloud Instance List", "../screenshots/cloud-infra/instance-list.png"),
        ("Network / Subnet Configuration", "../screenshots/cloud-infra/network-subnet.png"),
        ("Security Group Policy", "../screenshots/cloud-infra/security-group.png"),
        ("SSH Connection Test", "../screenshots/cloud-infra/ssh-test.png"),
    ],
    "docs/server-setup.md": [
        ("OS Information", "../screenshots/server/os-info.png"),
        ("Docker Service Status", "../screenshots/server/docker-status.png"),
        ("WordPress/MariaDB Containers Running", "../screenshots/server/docker-ps.png"),
        ("HTTP Test Result", "../screenshots/server/curl-result.png"),
    ],
    "docs/ansible-automation.md": [
        ("Ansible Version", "../screenshots/ansible/ansible-version.png"),
        ("Inventory Configuration", "../screenshots/ansible/inventory.png"),
        ("Ping Test Result", "../screenshots/ansible/ping-test.png"),
        ("Playbook Execution Result", "../screenshots/ansible/playbook-result.png"),
        ("WordPress/MariaDB Deployment Result", "../screenshots/ansible/wordpress-deploy-result.png"),
    ],
    "docs/validation-report.md": [
        ("Host Health Check", "../screenshots/validation/health-check.png"),
        ("Docker Status Check", "../screenshots/validation/docker-status.png"),
        ("HTTP Service Check", "../screenshots/validation/http-check.png"),
        ("Backup File Created", "../screenshots/validation/backup-created.png"),
        ("Recovery Test Result", "../screenshots/validation/recovery-result.png"),
    ],
}

START = "<!-- AUTO_IMAGES_START -->"
END = "<!-- AUTO_IMAGES_END -->"

def image_exists(markdown_path: str) -> bool:
    repo_path = markdown_path.replace("../", "")
    return (ROOT / repo_path).exists()

def build_image_section(items):
    lines = []
    lines.append("## 자동 반영 이미지")
    lines.append("")
    lines.append("아래 이미지는 screenshots/ 폴더에 파일이 업로드되면 자동으로 표시된다.")
    lines.append("")

    for title, image_path in items:
        lines.append(f"### {title}")
        lines.append("")

        if image_exists(image_path):
            lines.append(f"![{title}]({image_path})")
        else:
            lines.append(f"{image_path} 이미지가 아직 업로드되지 않았다.")

        lines.append("")

    return "\n".join(lines).strip() + "\n"

def update_doc(doc_path: str, items):
    path = ROOT / doc_path

    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    image_section = build_image_section(items)

    block = f"{START}\n{image_section}{END}"

    if START in content and END in content:
        before = content.split(START)[0]
        after = content.split(END)[1]
        content = f"{before}{block}{after}"
    else:
        content = content.rstrip() + "\n\n" + block + "\n"

    path.write_text(content, encoding="utf-8")

def main():
    for doc_path, items in IMAGE_SECTIONS.items():
        update_doc(doc_path, items)

    print("Documentation image sections updated successfully.")

if __name__ == "__main__":
    main()

