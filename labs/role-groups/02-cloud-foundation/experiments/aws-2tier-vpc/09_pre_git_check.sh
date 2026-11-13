#!/bin/bash
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -e

cd "$LAB_ROOT"

echo "======================================"
echo "Pre-Git Safety Check"
echo "======================================"

echo ""
echo "[1] Check required files"

REQUIRED_FILES=(
  "00_syntax_check.sh"
  "00_run_all.sh"
  "01_create_base_network.yml"
  "02_create_security_groups.yml"
  "03_create_compute.yml"
  "04_create_alb.yml"
  "05_validate.yml"
  "06_generate_inventory.yml"
  "07_check_web_servers.yml"
  "08_generate_report.yml"
  "09_pre_git_check.sh"
  "10_generate_examples.yml"
  "99_delete_all.sh"
  "README.md"
  ".gitignore"
)

for FILE in "${REQUIRED_FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo "OK: $FILE"
  else
    echo "MISSING: $FILE"
    exit 1
  fi
done

echo ""
echo "[2] Check dangerous files"

DANGEROUS_FILES=(
  "ansible-jjh-key"
  "ansible-jjh-key.pub"
  "inventory.ini"
)

for FILE in "${DANGEROUS_FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo "WARNING: $FILE exists. It should not be committed."
  else
    echo "OK: $FILE not found"
  fi
done

echo ""
echo "[3] Check generated output files"

GENERATED_OUTPUT_FILES=(
  "output/base_network.yml"
  "output/security_groups.yml"
  "output/compute.yml"
  "output/alb.yml"
  "output/validation.yml"
  "output/report.md"
)

for FILE in "${GENERATED_OUTPUT_FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo "WARNING: $FILE exists. It should be ignored or reviewed before Git commit."
  else
    echo "OK: $FILE not found"
  fi
done

echo ""
echo "[4] Check sanitized examples"

EXAMPLE_FILES=(
  "output/example/base_network.example.yml"
  "output/example/security_groups.example.yml"
  "output/example/compute.example.yml"
  "output/example/alb.example.yml"
  "output/example/validation.example.yml"
)

for FILE in "${EXAMPLE_FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo "OK: $FILE"
  else
    echo "MISSING: $FILE"
    exit 1
  fi
done

echo ""
echo "[5] Check git ignore rules"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git check-ignore ansible-jjh-key >/dev/null 2>&1 && echo "OK: ansible-jjh-key ignored" || echo "WARNING: ansible-jjh-key not ignored"
  git check-ignore ansible-jjh-key.pub >/dev/null 2>&1 && echo "OK: ansible-jjh-key.pub ignored" || echo "WARNING: ansible-jjh-key.pub not ignored"
  git check-ignore inventory.ini >/dev/null 2>&1 && echo "OK: inventory.ini ignored" || echo "WARNING: inventory.ini not ignored"
  git check-ignore output/base_network.yml >/dev/null 2>&1 && echo "OK: output/base_network.yml ignored" || echo "WARNING: output/base_network.yml not ignored"
  git check-ignore output/security_groups.yml >/dev/null 2>&1 && echo "OK: output/security_groups.yml ignored" || echo "WARNING: output/security_groups.yml not ignored"
  git check-ignore output/compute.yml >/dev/null 2>&1 && echo "OK: output/compute.yml ignored" || echo "WARNING: output/compute.yml not ignored"
  git check-ignore output/alb.yml >/dev/null 2>&1 && echo "OK: output/alb.yml ignored" || echo "WARNING: output/alb.yml not ignored"
  git check-ignore output/validation.yml >/dev/null 2>&1 && echo "OK: output/validation.yml ignored" || echo "WARNING: output/validation.yml not ignored"
else
  echo "SKIP: not inside a git repository"
fi

echo ""
echo "[6] Show current git status"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short
else
  echo "SKIP: not inside a git repository"
fi

echo ""
echo "======================================"
echo "Pre-Git Safety Check Completed"
echo "======================================"
