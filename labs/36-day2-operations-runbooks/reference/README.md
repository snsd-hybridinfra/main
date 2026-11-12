# Authoritative Operational Runbook Framework

`docs/runbooks/phase-1/` contains the minimum package-oriented Phase 1 operator baseline and is governed by `runbook-manifest.yaml`.

Runbooks define procedure and authority boundaries. They do not by themselves promote package implementation, runtime validation, evidence, acceptance, completion, or maturity.

Legacy root-level numbered-scenario procedures were removed with the numbered scenario framework. Reusable operating guidance must now be package-owned and added under this directory with an explicit package and test identifier.

Raw runtime belongs under ignored `.runtime/zero-trust/`. Only reviewed sanitized package evidence may be tracked. Live, mutating, destructive, or service-affecting actions require separate explicit authority.
