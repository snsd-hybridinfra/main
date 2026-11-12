# ADR: Finalize the L3 Execution Plan

- Status: Accepted
- Date: 2026-07-27
- Action: ZT-PROJECT-PLAN-001
- Scope: Repository governance and planning only

## Context

The repository has package authorities and bounded evidence, but needs one executable project plan that preserves current truth while defining how evidence could support a later maturity decision. The retired numbered-scenario model must not return as an execution or progress authority.

## Decision

1. `L3_ADVANCED` is the actual implementation and evidence target, not a current maturity claim.
2. `L4_OPTIMAL` remains `ROADMAP_ONLY` until separately implemented, runtime validated, and assessed.
3. `ZT-ARC-001` surrounds the package flow and is not a sequential implementation package.
4. Descriptive package-owned acceptance cases are the behavioral validation authority for all technical packages.
5. The authenticated 2026 KISA guide is a secondary inspection and hardening reference. Its seed mappings are planning-only; `ZT-GOV-MAP-001` owns comprehensive review and acceptance.
6. Planning, architecture, mapping, implementation, local validation, runtime validation, runtime acceptance, evidence, maturity, and compliance remain independent state dimensions.

## Consequences

- The Phase 0-5 roadmap, execution plan, dependencies, gates, risks, evidence plan, and target model are machine validated.
- No implementation or runtime state is promoted by this decision.
- A later L3 decision must be either evidence-supported or `L3_NOT_YET_ACHIEVED`; success is not forced.
- L4 diagrams, documents, or installed tools cannot establish implementation or maturity.

## Rejected alternatives

- Restoring numbered scenarios or a fixed completion count.
- Treating KISA mapping as compliance or certification evidence.
- Collapsing all state into one `PASS` value.
- Using a simple average to declare L3 maturity.
