#!/bin/bash
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -e

cd "$LAB_ROOT"

echo "======================================"
echo "Ansible Playbook Syntax Check"
echo "======================================"

for PLAYBOOK in \
  01_create_base_network.yml \
  02_create_security_groups.yml \
  03_create_compute.yml \
  04_create_alb.yml \
  05_validate.yml \
  06_generate_inventory.yml \
  07_check_web_servers.yml \
  08_generate_report.yml \
  10_generate_examples.yml
do
  echo ""
  echo "[CHECK] $PLAYBOOK"

  if [ "$PLAYBOOK" = "07_check_web_servers.yml" ]; then
    ansible-playbook --syntax-check -i inventory.ini "$PLAYBOOK"
  else
    ansible-playbook --syntax-check "$PLAYBOOK"
  fi
done

echo ""
echo "======================================"
echo "ALL SYNTAX CHECKS PASSED"
echo "======================================"
