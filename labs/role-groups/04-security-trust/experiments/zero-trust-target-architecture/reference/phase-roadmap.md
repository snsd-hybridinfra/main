
# Authoritative Phase Roadmap

| Phase | Name | Current state | Packages |
|---|---|---|---|
| PHASE_1 | Foundation and Verification Operations | PARTIALLY_VALIDATED | Actual: ZT-FND-001; ZT-NET-001 (`BOUNDED_DIRECTIONAL_INTERZONE_ACL`, `VALIDATED`, `ACCEPTED`); ZT-VIS-001 (`BOUNDED_SINGLE_NODE_SANITIZED_LOCAL_TELEMETRY`, `VALIDATED`, `ACCEPTED`); ZT-ID-001 (`BOUNDED_NON_PRODUCTION_TARGET`); ZT-CV-001 (`PARTIALLY_ACCEPTED`); ZT-RV-001 (`ACCEPTED_AT_BOUNDED_EC4`); and ZT-DEV-001, ZT-APP-001, ZT-DATA-001, ZT-SYS-001, ZT-AUTO-001 (`PARTIALLY_RUNTIME_VALIDATED`) |
| PHASE_2 | Centralized Identity and Visibility | IN_PROGRESS_PARTIAL_RUNTIME | ZT-VIS-002 (`PARTIALLY_IMPLEMENTED / PARTIALLY_VALIDATED / PARTIALLY_ACCEPTED`); ZT-USE-001, ZT-ID-002, ZT-APP-002, ZT-ACC-001, ZT-PEP-001, ZT-EFF-001 planned |
| PHASE_3 | Cross-Domain Policy Enforcement | NOT_STARTED | ZT-PIP-001, ZT-POL-002, ZT-NET-002, ZT-SYS-002, ZT-DEV-002, ZT-COR-001, ZT-INC-001, ZT-AUTO-002, ZT-RESP-001, ZT-REC-001 |
| PHASE_4 | IaC, Configuration as Code, and Policy as Code Convergence | NOT_STARTED | ZT-ONB-001, ZT-IAC-001, ZT-IAC-002, ZT-CFG-001, ZT-PAC-001, ZT-PAC-002, ZT-PAC-003, ZT-PAC-004, ZT-DRIFT-001, ZT-PLN-001, ZT-DEP-001 |
| PHASE_5 | Portability, Runbooks, Handoff, and Advanced Acceptance | NOT_STARTED | ZT-RUN-001, ZT-HOF-001, ZT-MAT-001, ZT-PLT-001, ZT-SCH-001 (`INSTALLED_DISABLED / DEFERRED_FINAL / 0_ACCEPTED_DATES`) |
| FUTURE_PHASE_6 | Optimal-Maturity Expansion | ROADMAP_ONLY | ZT-RISK-001, ZT-BA-001, ZT-PDP-002, ZT-PEP-002, ZT-AUTO-003, ZT-OPT-001, ZT-OPT-002 |

Phase 1 has `phase_scope_boundary: ZT-RV-001`, `phase_implementation_status: PARTIAL`, `phase_validation_status: PARTIALLY_VALIDATED`, and `phase_completion_status: COMPLETED_WITH_GAPS`. P1-ACC-001 is `ACCEPTED_WITH_GAPS` under `P1-RV-FRESHNESS-001`; stale RV evidence remains a mandatory final-gate risk. ZT-SCH-001 is installed and disabled with zero accepted scheduled dates and is deferred to the final Phase 5 gate. Phase 2 has reached bounded partial runtime in P2-VIS-001. One private OpenStack monitoring VM, four Terraform resources, five fixed components, mTLS, sanitized ingestion, restart persistence, package-only rollback, preserved-data recovery and cleanup are accepted at EC3. Alert delivery, elapsed-retention behavior and full Cinder snapshot rebuild/reattachment restore remain open, so P2-VIS-001 is not complete.

Actual evidence comes only from accepted package records and retained historical evidence. ZT-FND-001, ZT-NET-001, and ZT-VIS-001 are validated for bounded scopes; this does not change capability maturity. `ZT-NET-001` is `IMPLEMENTED` and `RUNTIME_VALIDATED`, with runtime validation `VALIDATED` and acceptance `ACCEPTED` for one `BOUNDED_DIRECTIONAL_INTERZONE_ACL`; broader segmentation, encryption, SDN, resilience, and production scope remain open. `ZT-VIS-001` is `IMPLEMENTED` and `RUNTIME_VALIDATED`, with runtime validation `VALIDATED` and acceptance `ACCEPTED` for four sanitized summary sources and one `BOUNDED_SINGLE_NODE_SANITIZED_LOCAL_TELEMETRY` stack; external NTP synchronization, continuous observation, central visibility, broad source onboarding, SIEM/SOC, and maturity remain open. `ZT-ID-001` is `IMPLEMENTED` and `RUNTIME_VALIDATED`, with runtime validation `VALIDATED` and acceptance `ACCEPTED` for one `BOUNDED_NON_PRODUCTION_TARGET`; centralized identity, MFA, OIDC, application RBAC, production validation, and maturity remain open.

`ZT-DEV-001` is `IMPLEMENTED` / `PARTIALLY_RUNTIME_VALIDATED` for six aliases and one mandatory VM; broad endpoint management, agents, automation, enforcement, and maturity remain open. `ZT-APP-001` is `IMPLEMENTED` / `PARTIALLY_RUNTIME_VALIDATED` for a bounded inventory, partial direct-image SBOM, and one unchanged Alloy pilot; immutable provenance, signing, transitive scanning, broad enforcement, and maturity remain open. `ZT-DATA-001` is `IMPLEMENTED` / `PARTIALLY_RUNTIME_VALIDATED` for seven metadata-only assets, manual labels, detection-only DLP, and one synthetic restore; platform encryption, live backup/restore, blocking DLP, continuous analysis, and maturity remain open. `ZT-SYS-001` is `IMPLEMENTED` / `PARTIALLY_RUNTIME_VALIDATED` for seven bounded system records, five safe matched configuration hashes, and existing fixed read-only validators; OpenStack remains `CURRENT_DEGRADED`, while complete PAM, credential lifecycle, continuous FIM, broad hardening, recovery, and maturity remain open. `ZT-AUTO-001` is `IMPLEMENTED` / `PARTIALLY_RUNTIME_VALIDATED` for fixed R0-R3 handlers, default-deny policy, deterministic planning, and one partial cross-domain read-only run; arbitrary execution, R4-R8 mutation, external notification, response automation, repeatability, scheduling, SOAR, and maturity remain open. `ZT-VIS-002` is bounded partial runtime at EC3 and does not inherit ZT-VIS-001 authority. `ZT-ID-002` is a later roadmap candidate, not a rename.

The ZT-VIS-002 partial promotion is independently hash-bound to sanitized live
evidence. It supplies no full acceptance, completion, maturity, compliance,
scheduled validation, central identity, or production credit.

```mermaid
flowchart LR
  P1["Phase 1: foundation and verification"] --> P2["Phase 2: identity and visibility"]
  P2 --> P3["Phase 3: cross-domain enforcement"]
  P3 --> P4["Phase 4: IaC, Configuration as Code, Policy as Code"]
  P4 --> P5["Phase 5: portability and acceptance"]
  P5 -. "separate future approval" .-> P6["Future Phase 6: Optimal roadmap"]
```

Entry and exit criteria are authoritative in `implementation-dependency-map.yaml`. No planned package is promoted by roadmap position.
