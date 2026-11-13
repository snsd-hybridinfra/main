
# ZT-ARC-001 Target Architecture

- Status: `DESIGN_ONLY` / `LOCAL_VALIDATED`
- Runtime validation: `NOT_VALIDATED`
- Authority status: `AUTHORITATIVE`
- Current maturity: `UNASSESSED`
- Target boundary: `ADVANCED_TARGET`
- Architecture designation: `OPTIMAL_READY` (repository-local, not an official maturity level)

This directory is the authoritative post-Phase-1 target architecture for the SNSD laboratory. It positions the project as an **IaC, Configuration as Code, and Policy as Code-driven Advanced Zero Trust Secure Operations Platform with an Optimal-Ready Extension Architecture**. The conservative public title is **Hybrid and Multicloud-Ready Secure Operations Platform** because AWS and Azure adapters are not implemented.

## Terms

- IaC = Infrastructure as Code: infrastructure desired state and provider adapters.
- CaC = Configuration as Code: versioned operating-system and service configuration. Here, CaC never means Compliance as Code.
- PaC = Policy as Code: deterministic design-time, deployment-time, and runtime policy evaluation.
- `ADVANCED_TARGET`: the selected capability is intended to satisfy official Advanced-stage conditions.
- `ADVANCED_VALIDATED`: capability-specific implementation and fresh runtime evidence support an Advanced-stage assessment.
- `OPTIMAL_READY`: stable local interfaces exist for future Optimal-stage functions. It is not `OPTIMAL`, and readiness does not establish maturity.

## Authority and Boundaries

The external authority is the local **제로트러스트 가이드라인 2.0** PDF whose recorded SHA-256 is in `../authoritative-source.md`. The repository taxonomy authority remains `../capability-catalog.yaml`; current truth remains `../current-baseline-assessment.yaml`; planning remains `../capability-implementation-backlog.yaml`.

The architecture represents all 52 canonical capabilities: 21 Advanced primary, 15 Advanced supporting, 4 Initial, 5 design-only, and 7 future Optimal-roadmap. No capability status or current maturity is promoted by this package.

Monitoring traces under `.runtime/zero-trust/zt-vis-002/` remain protected non-authorities. `ZT-VIS-002` is partially implemented, partially runtime validated, and partially accepted for one bounded private non-production OpenStack monitoring VM at EC3; its accepted sanitized authority excludes protected runtime values and retains three completion gaps.

Phase 1 remains bounded by the historical accepted `ZT-RV-001` EC4 result, with implementation `PARTIAL`, validation `PARTIALLY_VALIDATED`, and completion `COMPLETED_WITH_GAPS`. P1-ACC-001 is `ACCEPTED_WITH_GAPS` under `P1-RV-FRESHNESS-001`; the historical three-run window remains stale, while the new manual refresh is 1/3 at EC3, and the gap must close before final scheduling or P5-ACC-001. Phase 2 is `IN_PROGRESS_PARTIAL_RUNTIME` for P2-VIS-001. ZT-SCH-001 is installed, disabled, and deferred to the final Phase 5 gate before P5-ACC-001; it provides no EC5 credit. ZT-FND-001, ZT-NET-001, and ZT-VIS-001 are validated only for their bounded package scopes. `ZT-ID-001` is runtime accepted only for one bounded non-production validator endpoint; centralized identity, MFA, OIDC, application RBAC, production validation, and maturity remain open. `ZT-AUTO-001` is implemented and partially runtime validated only for fixed R0-R3 handlers and one partial cross-domain read-only run; mutation, external notification, autonomous response, repeatability, scheduling, SOAR, and maturity remain open. `ZT-VIS-002` does not inherit ZT-VIS-001 authority and cannot be completed until alert-delivery, elapsed-retention, and full Cinder snapshot-restore gaps close.

## Navigation

- Scope and selection: `advanced-maturity-scope.md`, `capability-selection-method.md`, `capability-traceability-matrix.md`
- Platform architecture: `iac-cac-pac-reference-architecture.md`, `target-portability-architecture.md`
- Contracts: `host-onboarding-contract.md`, `operator-interface-contract.md`
- Assessment: `advanced-maturity-acceptance-model.md`, `handoff-acceptance-model.md`
- Roadmaps: `phase-roadmap.md`, `optimal-expansion-roadmap.md`
- Execution model: `golden-path.md`, `implementation-dependency-map.md`
- Authoritative operational runbooks: `../../runbooks/RUNBOOK_INDEX.md`
