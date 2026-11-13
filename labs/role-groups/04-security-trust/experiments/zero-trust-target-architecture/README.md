# Lab 46: Zero Trust Target Architecture and Acceptance Maps

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. Extracted **all 26** source files from `docs/zero-trust/target-architecture/`, covering design/portability, target selection and handoff, maturity roadmap, bounded host-onboarding, control dependencies and operator interface contracts.

## Scope and intended reuse
- Trace capabilities → implementation requirements → tests, evidence, approval and rollback conditions
- Review IaC/CaC/PaC architecture, workload identity and access paths
- Decide which network/security behaviors belong in Labs 17, 21, 22, 32, 38, 44 and 45
- Keep *target designs* separate from what was actually deployed and tested

## Large source matrices included
All three larger YAML/JSON-compatible matrices previously excluded are now included under `reference/`: maturity acceptance, capability selection and capability traceability. Their presence is a **design reference**, not runtime maturity or compliance proof.

The KISA mapping references were also extracted into `reference/kisa-mapping/`. These are technical mapping examples; they do not demonstrate guideline compliance, approval or a current certified control.

## Next
Build concise, smaller machine-verifiable control contracts; eliminate source-root hardcoded dependencies. Add deterministic negative tests on missing evidence and approval, and require independent lab evidence before accepting a capability.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No architecture claims of current operational validation.
