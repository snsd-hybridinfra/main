# ADR-0002: Non-Production Runtime Evidence Boundary

- Status: ACCEPTED
- Date: 2026-07-16
- Decision Type: Scope and evidence boundary clarification

## Context

The foundation scope prohibited repository-driven access to real cloud
resources, while the scenario model also requires reviewable evidence from an
operator-authorized disposable lab. retired-numbered-case now has real OpenStack AIO execution
results supplied by the operator, but the repository must not retain raw
terminal output, credentials, generated authentication files, state, or unique
environment identifiers.

## Decision

1. Runtime infrastructure actions remain outside repository automation unless
   separately authorized.
2. An operator may supply results from an observed non-production lab run.
3. The repository may store only normalized, text-only, sanitized evidence
   mapped to an existing retired numbered scenario framework scenario.
4. Tokens, passwords, authentication files, UUIDs, MAC addresses, dynamic IPs,
   account identifiers, private keys, and raw output are prohibited.
5. Planned Terraform reproduction, teardown, HA, backup, monitoring, security
   hardening, and cross-platform integration remain separate validations.
6. Local repository linting cannot substitute for runtime evidence.

## Consequences

- retired-numbered-case may record the verified Kolla-Ansible AIO control-plane and end-to-end
  Neutron network results without adding cloud credentials or provisioning
  automation.
- The existing retired numbered scenario framework list does not change.
- retired-numbered-case, retired-numbered-case, retired-numbered-case-retired-numbered-case, and other related scenarios retain their own
  acceptance criteria and statuses.
- Reviewers can distinguish operator-supplied runtime evidence from repository
  structure checks and from planned implementation.

## Non-Production Boundary

This decision applies only to the disposable portfolio lab. It does not
authorize production deployment, public-cloud spend, formal compliance claims,
or autonomous infrastructure changes.
