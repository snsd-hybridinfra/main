# AWS Security Group Least Privilege Baseline

This non-production baseline defines repository-side rule expectations only. It does not represent a deployed AWS Security Group.

## Inbound Principles

- Default deny inbound principle: no inbound traffic is permitted unless an explicit required rule is documented.
- Explicit allow only for required service ports.
- SSH access is allowed only from `<management-cidr>` or `<bastion-security-group-id>`.
- No public SSH from `0.0.0.0/0`.
- No public RDP from `0.0.0.0/0`.
- No public database access from `0.0.0.0/0`.
- HTTP/HTTPS public exposure is allowed only for `<public-web-security-group>`.
- Internal service access must use `<aws-vpc-cidr>`, `<private-service-security-group>`, or another approved security-group reference placeholder.
- Database access is restricted to `<database-security-group>` relationships documented in the rule matrix.

## Egress Principle

Egress must be documented and justified. The example matrix permits only a reviewable HTTPS update path; unrestricted egress is not implied by this baseline.

## Evidence Collection Model

- Record matrix parsing, dangerous-port checks, Terraform placeholder checks, sensitive-content checks, and execution boundaries at `<evidence-path>` through standalone-lab evidence.
- Do not capture AWS account IDs, credentials, real addresses, live Security Group output, state, or plans.
