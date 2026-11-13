
# Project Objective

Analyze all 52 detailed capabilities in the Korean Zero Trust Guideline 2.0, select capabilities that can be credibly implemented in the laboratory, implement and validate those selected capabilities at the official Advanced maturity stage, and integrate them into a portable secure operations platform driven by Infrastructure as Code, Configuration as Code, and Policy as Code.

The architecture supports future expansion toward the official Optimal maturity stage without asserting that Optimal maturity has been implemented.

## Operating Model

The user owns only physical or manual prerequisites that Codex cannot perform safely: resource allocation, disk or interface attachment, base OS installation, console-only work, initial management access, interactive secret entry, and destructive or service-affecting approval.

Codex owns repository inspection, architecture, IaC/CaC/PaC design and implementation, deployment tooling, validators, tests, runtime validation, sanitized evidence, runbooks, documentation, and status maintenance. Repository or configuration work is not delegated to the user.

## Definitions

- Infrastructure as Code (IaC) manages infrastructure desired state.
- Configuration as Code (CaC) manages versioned host and service configuration; CaC does not mean Compliance as Code here.
- Policy as Code (PaC) evaluates design, proposed deployment, and runtime state.
