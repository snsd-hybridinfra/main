# Lab 46: Zero Trust Target Architecture and Acceptance Maps

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. Extracted **23 of 26** source files from `docs/zero-trust/target-architecture/`, covering design/portability, target selection and handoff, maturity roadmap, bounded host-onboarding, control dependencies and operator interface contracts.

## Scope and intended reuse
- Trace capabilities → implementation requirements → tests, evidence, approval and rollback conditions
- Review IaC/CaC/PaC architecture, workload identity and access paths
- Decide which network/security behaviors belong in Labs 17, 21, 22, 32, 38, 44 and 45
- Keep *target designs* separate from what was actually deployed and tested

## Intentionally omitted
The three largest original generated-looking matrices were not copied here, pending a need and an independent size/uniqueness/security check:
- `advanced-maturity-acceptance-model.yaml` (~64 kB)
- `capability-selection.yaml` (~131 kB)
- `capability-traceability-matrix.yaml` (~141 kB)

Their source blob hashes and paths are indexed in `docs/migration/snsd-multicloud-ops-source-file-manifest.tsv`, **not backed up there**. The original repository remains necessary.

## Next
Build concise, smaller machine-verifiable control contracts; eliminate source-root hardcoded dependencies. Add deterministic negative tests on missing evidence and approval, and require independent lab evidence before accepting a capability.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No architecture claims of current operational validation.
