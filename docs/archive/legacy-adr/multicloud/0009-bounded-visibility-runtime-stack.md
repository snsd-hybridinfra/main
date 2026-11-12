# ADR: Bounded Visibility Runtime Stack

- Status: Accepted for the disposable laboratory
- Date: 2026-07-22
- Scope: ZT-VIS-001 persistent-storage closure and later Phase 1 package evidence

## Context

`ZT-VIS-001` has a deterministic local normalization and correlation pipeline,
but no accepted persistent central log store. The approved monitoring VM is
running Ubuntu 24.04 with a root-managed Docker runtime, no application
containers, and enough bounded laboratory capacity. The target architecture
already identifies Grafana, Loki, and Alloy as candidate visibility
components.

## Decision

Deploy one pinned, single-node Grafana/Loki/Alloy stack on the dedicated
monitoring VM. Loki stores only approved sanitized event streams with a
14-day retention window. Alloy reads only the dedicated sanitized-event
directory. Grafana uses file-provisioned Loki configuration, disables
anonymous access and self-registration, and reads its administrator secret
from a VM-local root-owned file outside Git.

The stack uses a private Docker network, no host networking, no privileged
container, no Docker socket mount, no broad host-log mount, no external
notification integration, and no automated blocking or remediation. Runtime
data and secrets remain on the VM. Repository files contain configuration and
placeholders only.

## Validation and evidence boundary

Configuration existence is not runtime validation. Runtime acceptance
requires pinned image identities, healthy containers, a successful Loki write
and query using a synthetic sanitized record, Grafana health, Alloy health,
persistent-volume evidence, retention configuration, and a sanitized result.
This decision does not establish an enterprise SIEM, UEBA, continuous trust
evaluation, EC6 continuous observation, or capability maturity.

## Rollback

Stop and remove only the `snsd-zero-trust-visibility` Compose project. Preserve
the VM, Docker runtime, operator SSH access, repository validators, and any
reviewed evidence. Data directories are retained until separately approved
for deletion.

## Consequences

The monitoring VM becomes a Phase 1 shared evidence service. It is not a
production monitoring platform and must not be used to store credentials,
raw validator output, personal information, or unapproved host logs.
