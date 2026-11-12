# Lab 15: AWS 2-Tier VPC with Ansible

**Status:** `MIGRATED / NOT_REVALIDATED` (2026-11-11). Extraction and static hardening only; not deployed in the destination.

## Question
Can Ansible build a multi-AZ VPC, private web EC2 hosts behind an ALB, restricted Bastion access, validation reports, and safely scoped cleanup?

## Components
- `01_create_base_network.yml`: VPC, private/public subnets, routes, NAT gateway
- `02_create_security_groups.yml`: ALB, Bastion and private web access policies
- `03_create_compute.yml`: EC2, generated SSH key and web services
- `04_create_alb.yml` through `08_generate_report.yml`: traffic, validation, inventory and report
- `09_pre_git_check.sh`, `10_generate_examples.yml`: pre-commit safety check and synthetic outputs
- `99_delete_all.sh`: charge-bearing resources cleanup (explicit opt-in)

## Migration changes
- Source-specific `/home/user1/lab/aws` paths changed to `{{ playbook_dir }}` (Ansible) or script-local `LAB_ROOT`.
- Bastion SSH ingress now requires `LAB_MANAGEMENT_CIDR`; unset and `0.0.0.0/0` values are rejected.
- SSH host-key checking uses `accept-new` instead of disabling verification. Confirm fingerprints before use.
- The cleanup script requires `CONFIRM_LAB_DESTROY=YES` and must be reviewed before execution.
- Real inventory, private keys, credentials, endpoint IDs and generated reports must remain untracked.

## Verification plan
1. Verify syntax and module collection versions using `00_syntax_check.sh`.
2. Review AWS account, IAM scope, costs (especially NAT Gateway, EC2 and ALB) and `ap-northeast-2` region.
3. Set `LAB_MANAGEMENT_CIDR` to your own trusted IPv4 CIDR, typically a /32.
4. Run only in a disposable AWS account; check provision → ALB response → denied public web SSH → report → cleanup.
5. Store redacted evidence and record limitations before upgrading status to `LOCAL_VALIDATED`.

## Provenance
Extracted and adapted from private `snsd-hybridinfra/test` at commit `6147e9114e79aed5034be2bcd9ee1f6e7b4a695f`, source `ansible-aws-2tier-vpc-lab/`. Its duplicate nested copy was not migrated. This lab is not an evidence-backed continuation of source environment execution.

## Future combinations
Reusable with the IAM/STS and Terraform security labs, once integration is tested independently.


## Added source fixtures (2026-11-12)
Five historical `output/example/*.example.yml` synthetic AWS output examples are now preserved under `fixtures/examples/`. These are example expected shapes, **not rerun AWS evidence**.
