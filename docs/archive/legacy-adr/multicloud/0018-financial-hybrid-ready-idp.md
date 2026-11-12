# ADR 0018: Financial Hybrid-Ready Internal Developer Platform

- Status: Accepted
- Date: 2026-08-27
- Decision authority: operator-approved project architecture change under `ZT-ARC-001`

## Context

The repository began as a scenario-centered security project, then moved to package-centered Zero Trust governance while accumulating OpenStack, k3s, portal, GitOps, observability and automation assets. The root definition still treated security validation as the product, leaving the platform assets without a single product goal.

The selected direction is a virtual securities-company Internal Developer Platform resembling a financial hybrid-cloud operating model: users consume governed IaaS and PaaS products through a self-service control plane, while infrastructure, configuration, policy and lifecycle operations remain auditable and recoverable.

## Decision

Make the Financial Hybrid-Ready IDP the primary product. Use OpenStack as the private IaaS plane and k3s as the PaaS plane. Use Terraform, Ansible, GitOps and CI/CD as distinct automation responsibilities. Design the financial network underlay around Nexus NX-OS and IOS-XE capabilities, including segmented management, dynamic routing and bounded multicast.

Keep Zero Trust as the cross-cutting security and validation plane. Existing ZT package IDs, status, validators and sanitized evidence remain authoritative for their recorded scopes. This decision creates no new ZT package ID and grants no status promotion.

Use provider-neutral adapter contracts for future public-cloud connectivity. Until a provider is selected and a connection is implemented and runtime validated, describe the architecture as `Hybrid-Ready`, never as an operating hybrid cloud.

Adopt existing `applications/internal-iaas-portal/` and `platform/` content only through reconciliation against the new root baseline. File presence is not integration or runtime evidence.

## Consequences

- The root README, project definition, scope and architecture become platform-first.
- Financial transaction processing and production brokerage systems remain out of scope; synthetic workloads will be used.
- Licensed NX-OS/IOS images, credentials, state and raw runtime data remain outside Git.
- A separate DR site and DR fabric are excluded. Backup, restore and declarative rebuild remain data-protection controls without a DR availability claim.
- Existing Zero Trust and Phase status truth is preserved.
- The next work is contract and asset reconciliation, then bounded local integration. Live mutation still requires separate authorization.

## Supersession and compatibility

This ADR changes the primary product framing and supersedes any statement that the repository is only a Zero Trust validation product. It does not invalidate ADR 0012 or the Zero Trust architecture ADRs; those become component and security-plane decisions inside the new product architecture.
