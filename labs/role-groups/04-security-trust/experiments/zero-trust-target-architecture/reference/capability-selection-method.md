
# Capability Selection Method

## Inputs

Selection uses the canonical 52-capability catalog, the current baseline, current sanitized evidence, backlog dependencies, the official capability-specific maturity tables, laboratory constraints, and the Golden Path.

## Decision Tests

An Advanced primary target must directly support the Golden Path, be implementable in the lab, produce runtime evidence, be operable through IaC, Configuration as Code, or Policy as Code, and avoid unsupported enterprise assumptions. Supporting targets pass the same tests with a narrower evidence or enforcement boundary.

Initial targets cannot presently satisfy all Advanced-stage characteristics. Design-only items need enterprise lifecycle or organizational scale. Optimal-roadmap items depend on dynamic risk, behavior analytics, large-scale endpoint telemetry, adaptive authorization, predictive intelligence, or bounded closed-loop response.

## Independence of State

Selection, target maturity, current implementation, current validation, evidence authority, and current maturity are independent. A selected target never promotes current state. Reassessment occurs only through `advanced-maturity-acceptance-model.yaml`.
