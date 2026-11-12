
# ADR: IaC, Configuration as Code, and Policy as Code Responsibility Boundaries

- Status: Accepted for target architecture
- Date: 2026-07-18
- Scope: ZT-ARC-001 design only

## Context

The post-Phase-1 platform needs a portable, evidence-based target without promoting current implementation or maturity.

## Decision

IaC owns infrastructure desired state; Configuration as Code owns host/service state; Policy as Code owns deterministic decisions; secrets and raw runtime state stay external.

## Evidence and Runtime Boundary

Architecture is `DESIGN_ONLY`. Capability maturity remains `UNASSESSED` until configuration, runtime, enforcement where applicable, repeatability, failure, rollback/recovery, freshness, and sanitized evidence requirements pass.

## Consequences

Implementations must use the target profiles, phase gates, operator contract, runbooks, and capability-specific acceptance model. Active monitoring work and existing runtime evidence remain unchanged.

## Rejected Alternatives

Overlapping ownership and repository-held secrets were rejected.
