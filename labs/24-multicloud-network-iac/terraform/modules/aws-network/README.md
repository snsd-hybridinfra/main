# AWS Network Module Placeholder

This module defines a non-production review structure for standalone-lab. It includes placeholders for a VPC, public and private subnets, route tables, an internet gateway, and an empty baseline security group.

## Safety Boundary

- No provider or backend block is defined here.
- No credentials, account identifiers, remote state, or live resource values are included.
- The security group intentionally has no traffic rules; least-privilege rules belong to standalone-lab.
- standalone-lab does not run `terraform init`, `plan`, `apply`, or `destroy`.
- Provider validation belongs to standalone-lab.

The module is suitable for repository review and formatting checks only until a later scenario explicitly authorizes provider configuration and lab execution.
