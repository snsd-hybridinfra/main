# ADR 0019: Approved Composite Service Catalog

- Status: Accepted
- Date: 2026-08-27
- Decision authority: explicit operator approval of the catalog construction model
- Architecture authority: `ZT-ARC-001`

## Context

The portal candidate currently exposes five OpenStack-bound VM and k3s entries. They are useful deterministic execution profiles, but they are too close to provider modules to represent the final developer experience. The selected IDP model should deliver business-meaningful services assembled from governed components without allowing arbitrary user composition.

## Decision

Use a two-level catalog:

```text
Internal service components
  -> operator-approved composite blueprints
  -> limited user inputs
  -> immutable resolved deployment manifest
  -> one correlated lifecycle and rollback decision
```

Fix eight internal service components and eight initial user-facing blueprints in `docs/platform/composite-service-catalog.yaml`. Components are not directly user selectable. Users select one approved blueprint and may provide only bounded environment, size, duration and purpose values allowed by that blueprint.

The five entries in `applications/internal-iaas-portal/terraform/catalog.json` remain provider-bound execution profiles. They are implementation inputs selected by the future blueprint resolver, not the final user-facing product catalog.

Free-form component assembly, arbitrary Terraform/HCL, raw provider identifiers, user-selected security controls and partial-success deployment are denied. A blueprint is one deployment unit: failure triggers reverse-order rollback, and rollback failure remains explicit.

## Consequences

- Product count is controlled by approved blueprints rather than every possible component combination.
- Common network policy and operations controls are mandatory in every blueprint.
- VDI becomes a composed workspace service, not merely a raw VM size.
- Synthetic market-data multicast is limited to one explicit non-production blueprint.
- Blueprint discovery and deterministic resolution are locally implemented and tested. `VM_APPLICATION_STACK` carries its immutable manifest through request, approval and independent runner verification; the remaining blueprints fail closed until every component adapter exists.
- This decision does not authorize live provisioning or change any Zero Trust package status.
