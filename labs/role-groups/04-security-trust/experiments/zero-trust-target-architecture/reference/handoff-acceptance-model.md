
# Handoff Acceptance Model

A clean operator must select a target type, copy an approved profile, enter environment settings, prepare secrets outside Git, run preflight, generate a plan, review policy, record approval, deploy, validate, find sanitized evidence, detect drift, reconcile with approval, roll back, and recover.

Acceptance requires no hidden manual step, author-specific path, personal account, reusable-module management address, shared password, repository secret, or source modification. Profile validation must be deterministic; failure, rollback, evidence, VM-versus-physical distinctions, and repeat behavior must be explicit.

The current status is `DESIGN_SPECIFICATION` / `NOT_IMPLEMENTED`. A document review is not a clean-environment or clean-operator result. See `handoff-acceptance-model.yaml`.
