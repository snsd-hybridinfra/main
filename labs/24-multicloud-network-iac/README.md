# Lab 24: AWS & Azure Network IaC Baselines

**Status:** `MIGRATED / NOT_REVALIDATED`. This is the two-provider Terraform network reference extracted from a prior multi-cloud experiment, **not a validated cross-cloud network**.

## Source modules
- `terraform/modules/aws-network/`: VPC, subnets, gateway, route table, empty security baseline
- `terraform/modules/azure-network/`: resource group, VNet, subnets, NSG, route table
- `terraform/envs/{aws,azure}-network-validation/`: intended example consumers and tfvars templates
- `security-baseline/`: source least-privilege policy guidance

## Test order
1. Confirm Terraform/provider versions and module input/output compatibility. Run `terraform fmt -check`, `terraform init -backend=false`, `terraform validate` per cloud using only approved public providers.
2. Never apply until reviewing a short-lived test account, spend limits, CIDR/address overlap and least privilege.
3. For each provider, collect redacted plans, denied network policies and resource destruction/rollback outcomes. **Do not commit tfstate, credentials, resource IDs or service principals.**
4. AWS and Azure networking are **independent tracks**. Connectivity between the two was not supplied or validated.

## Why separate from Lab 15?
Lab 15 uses Ansible for AWS orchestration; this lab compares Terraform constructs and network guardrails. Do not assume both descriptions agree without testing.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
