#!/bin/bash
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -e

cd "$LAB_ROOT"

echo "======================================"
echo "Ansible AWS 2-Tier VPC Automation Lab"
echo "======================================"

echo "[1/8] Create base network"
ansible-playbook 01_create_base_network.yml

echo "[2/8] Create security groups"
ansible-playbook 02_create_security_groups.yml

echo "[3/8] Create compute resources"
ansible-playbook 03_create_compute.yml

echo "[4/8] Create application load balancer"
ansible-playbook 04_create_alb.yml

echo "[5/8] Validate infrastructure"
ansible-playbook 05_validate.yml

echo "[6/8] Generate Ansible inventory"
ansible-playbook 06_generate_inventory.yml

echo "[7/8] Check private web servers through bastion"
ansible-playbook -i inventory.ini 07_check_web_servers.yml

echo "[8/8] Generate final report"
ansible-playbook 08_generate_report.yml

echo "======================================"
echo "DONE"
echo "======================================"

echo "Output files:"
ls -l $LAB_ROOT/output

echo ""
echo "Generated inventory:"
ls -l $LAB_ROOT/inventory.ini

echo ""
echo "ALB DNS:"
grep dns_name $LAB_ROOT/output/alb.yml || true

echo ""
echo "Final report:"
ls -l $LAB_ROOT/output/report.md
