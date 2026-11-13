# Bounded Identity Validation

This directory is the repository-local policy implementation for ZT-ID-001.
It defines a synthetic identity inventory contract, least-privilege roles,
authentication assurance requirements, lifecycle rules, deterministic access
decisions, sanitized evidence requirements, and lockout safeguards.

The authoritative package record is
[`zt-id-001-package.yaml`](../packages/zt-id-001-package.yaml), and the package
description is
[`zt-id-001-bounded-identity-validation.md`](../packages/zt-id-001-bounded-identity-validation.md).

## Authority boundaries

- All identity records are synthetic local fixtures.
- Secret values are prohibited; only approved external-reference schemes are
  accepted.
- `ALLOW` means the local policy evaluator accepted a synthetic request. It
  never grants live access.
- MFA and OIDC are policy requirements marked not implemented.
- No runtime adapter is implemented. SSH, Linux, OpenStack, Keycloak, Grafana,
  and certificate inspection remain future interfaces requiring separate
  approval.
- No current capability maturity is assigned.

## Files

- `identity-subject-model.yaml` — synthetic subject inventory contract and
  accepted examples.
- `role-policy-matrix.yaml` — role, action, approval, and separation rules.
- `authentication-assurance-model.yaml` — authentication categories and target
  assurance requirements.
- `identity-lifecycle-policy.yaml` — lifecycle states, transitions, and review
  behavior.
- `decision-policy.yaml` — deterministic decision fields and evaluation order.
- `evidence-contract.yaml` — sanitization, retention, privacy, and authority
  rules.
- `rollback-and-lockout-safety.md` — current rollback and future live safety
  gates.

Run the read-only local validator with:

```powershell
python tools/validate_zt_id_001.py --verbose --strict --format text
```
