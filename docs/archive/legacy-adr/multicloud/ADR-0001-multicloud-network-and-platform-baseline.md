# ADR-0001: Multi-Cloud Network and Platform Baseline

- Status: ACCEPTED (EVE-NG and one OpenStack AIO network path partially implement the baseline)
- Date: 2026-07-15
- Decision Type: Architecture and planning normalization
- Implementation Effect: None by itself

## Context

The repository had a minimum local-lab reference, but it did not provide one
authoritative phase order or explicit responsibility, CIDR, cost, lifecycle, and
external-exposure boundaries for EVE-NG, OpenStack, AWS, Azure, local Kubernetes,
and local MariaDB.

Some valid evidence was already collected on a flat Bootstrap Management
Network. That evidence must be retained without being mistaken for completed
service-zone migration.

## Decision

1. EVE-NG is the On-Prem network-control axis.
2. OpenStack is the Private Cloud axis.
3. AWS and Azure are minimum, cost-bounded public-cloud validation environments.
4. Local Kubernetes is the application runtime.
5. Local MariaDB is the internal primary/replica data platform.
6. External exposure is optional and limited to HTTP/HTTPS.
7. Planned aggregates are `10.10.0.0/16` (On-Prem), `10.20.0.0/16`
   (OpenStack), `10.30.0.0/16` (AWS), `10.40.0.0/16` (Azure), and optional
   `10.255.0.0/16` (WireGuard).
8. The OpenStack provider/external CIDR must be discovered from the lab rather
   than invented. The retired-numbered-case run established the approved VLAN 70 provider
   subnet while dynamic router and Floating IP values remain masked.
9. Actual bootstrap runtime CIDR/host addresses and the external address remain
   masked under repository policy.
10. Infrastructure follows Plan, Apply, Validate, sanitized evidence, Destroy,
    and cleanup verification.

## Alternatives Considered

- Use AWS/Azure as full application platforms: rejected for cost and scope.
- Make OpenStack optional: rejected because Private Cloud is a core platform
  axis.
- Replace existing bootstrap evidence after migration: rejected because evidence
  remains valid for the observed bootstrap state.
- Require WireGuard: rejected; connectivity method remains optional.
- Commit actual bootstrap addresses: rejected by repository sensitive-data rules.

## Consequences

- One canonical Lab Phase 0-10 sequence is maintained in
  `docs/lab-build-order.md`.
- AWS/Azure resource counts and prohibited services are explicit.
- Planned CIDRs are non-overlapping, while bootstrap/provider conflicts remain
  explicit local/discovery checks.
- retired-numbered-case, retired-numbered-case, retired-numbered-case, retired-numbered-case, and retired-numbered-case are planned for network-path revalidation
  after service-zone migration.
- retired-numbered-case/retired-numbered-case are not repeated solely for renumbering unless runtime configuration
  changes.
- No scenario status changes merely because this ADR is accepted; retired-numbered-case and
  retired-numbered-case advance only through their separate evidence packages.

## Validation and Review

Review the architecture documents for internal consistency, run repository
validators, and repeat CIDR conflict checks before any apply. This ADR remains
a decision record, not implementation evidence; runtime evidence is held by
retired-numbered-case and retired-numbered-case.

## Non-Production Disclaimer

The decision governs a disposable portfolio lab and does not authorize cloud
spend, public exposure, production deployment, or compliance claims.
