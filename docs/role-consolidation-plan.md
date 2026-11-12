# Operational Role Consolidation Plan

**Date:** 2026-11-12 KST · **Review branch:** `chore/portfolio-structure-2026-11` · **Base PR:** #3

## Decision
**51 labs are assigned to 7 mutually exclusive primary role groups**. New role pages, a machine-readable manifest and common interface contract become the navigation and future integration layer. The old numbered lab folders remain the single source for code/tests/evidence so that a physical relocation does not break older references or erase original test boundaries.

## Role groups

| Role | Included labs | Count | What becomes shared |
|---|---|---:|---|
| [Network Fabric](../labs/role-groups/01-network-fabric/README.md) | 01, 02, 08, 09, 10, 12, 33, 43 | 8 | Topology, routing, failure and failover matrices |
| [Cloud Foundations](../labs/role-groups/02-cloud-foundation/README.md) | 14, 15, 16, 17, 23, 24, 39, 50, 51 | 9 | Provider-neutral network intent, IaC gates, safe provisioning |
| [Platform Delivery](../labs/role-groups/03-platform-delivery/README.md) | 25, 27, 28, 29, 30, 31, 34, 35, 49 | 9 | IDP request/approval/grant/provision/deploy lifecycle |
| [Security and Trust](../labs/role-groups/04-security-trust/README.md) | 04, 06, 07, 11, 13, 32, 38, 40, 46 | 9 | Principal, policy, device/role trust, deny evidence |
| [Observability SRE](../labs/role-groups/05-observability-sre/README.md) | 18, 19, 26, 42, 44 | 5 | Synthetic metrics/logs/probes, triage, alert quality |
| [Change Automation](../labs/role-groups/06-change-automation/README.md) | 03, 21, 22, 36, 37, 45, 47 | 7 | Safe read, approval, change plan, evidence freshness/CI |
| [Recovery DR](../labs/role-groups/07-recovery-dr/README.md) | 05, 20, 41, 48 | 4 | Backup snapshots, isolated restore, measured recovery |
| **Total** | **51 unique IDs** | **51** | No overlapping primary assignments |

## Duplicate consolidation targets (design, not implemented)

| Related labs | Consolidated functional entry | What remains separate |
|---|---|---|
| 01 + 02 + 10 + 33 | Network fabric/digital twin scenario and route/overlay validation | Vendor-specific CLI evidence |
| 15 + 24 + 50 + 16 | Provider-neutral cloud networking and multi-provider provisioning | AWS/Azure/OpenStack credentials and provider adapters |
| 17 + 32 + 38 + 40 + 46 | Policy and identity/control traceability | Source standards, bounded validation status |
| 18 + 26 + 44 + 19 + 42 | Synthetic metrics/logs and incident triage | Host installs, feature flags and access policy |
| 03 + 21 + 22 + 45 + 37 + 47 | Read-only inventory → approval → bounded change evidence | Remote writes, CI auto-push, production devices |
| 27 + 28 + 29 + 34 + 35 + 49 + 31 | IDP API → DB → approval → Terraform job → delivery | Separate service processes and privilege boundaries |
| 05 + 20 + 41 + 48 | Restic snapshot, verification, isolated recovery | Maintenance/prune/forget and database replacement rights |

## Migration closure / exclusions
- Included: original reusable tools, documented example configs, policy matrices, API contract tests, selected schema/migrations, CI patterns and architecture ADR references.
- Intentionally not bulk-copied: historical Zero Trust execution/recovery evidence (possible identifiers, inconsistent validation authority), imported team Eclipse UI source/assets pending rights review, Dandelion screenshots, slides and team activity records.
- These exclusions are **not lost**: the original repositories must remain. A file-path/SHA manifest is NOT a full Git backup.

## Quality gates
- [x] 51 primary ownership assignments in [manifest.json](../labs/role-groups/manifest.json), unique and covering all lab IDs
- [x] Seven role READMEs with integration input/output, mandatory failure/denial cases
- [x] Original numbered labs kept as canonical source files
- [ ] Group integration workflows implemented and tests re-run
- [ ] Full secret/license scan, source history mirror, restore verification
- [ ] PR reviewed and merged, then source repo cleanup separately approved

**No lab or role-group integration status is promoted by this organizational change.**
