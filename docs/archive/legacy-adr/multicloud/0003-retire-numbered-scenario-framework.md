# ADR-0003: Retire the numbered scenario framework

- Status: Accepted by explicit user instruction
- Date: 2026-07-27
- Action: ZT-SCN-RETIRE-001

## Decision

Remove the numbered scenario definitions, dedicated evidence tree, matrices, aggregate tooling, and scenario-only tests from the active repository. Do not create a successor scenario series.

## Replacement

Zero Trust packages, canonical capabilities, technical targets, validators, sanitized evidence, and explicit status decisions are the active authorities. Phase 1 follows the package flow registered in `docs/zero-trust/package-flow.yaml`; ZT-ARC-001 surrounds but does not precede that sequence.

## Consequences

- Git history is the only recovery source for deleted scenario artifacts.
- Existing package evidence is retained.
- Scenario-based progress and aggregate results are no longer meaningful.
- ZT-GOV-MAP-001 may later establish the authenticated KISA mapping layer without reintroducing scenarios.
- No package status or maturity is promoted by this retirement.
