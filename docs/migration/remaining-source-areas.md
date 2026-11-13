# Remaining Unique Source Areas: snsd-multicloud-ops

**Observed:** 2026-11-12 (KST)  
**Pinned source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`  
**Destination:** `snsd-hybridinfra/main` draft PR #3, 51 numbered lab directories and 7 operational role groups

The source has **1,252 tracked files** on its `main` branch. The extracted labs are **not a byte-identical replacement** and do **not** include Git commit history, other branches/tags, issues, pull requests, releases or external assets.

## Subtrees with full source-file copies in Labs 34–40

| Original subtree | Files | Destination |
|---|---:|---|
| `applications/internal-iaas-portal/database/` | 26 | [Lab 34](../../labs/role-groups/03-platform-delivery/experiments/postgres-schema-migrations/README.md) |
| `docs/runbooks/` | 40 | [Lab 36](../../labs/role-groups/06-change-automation/experiments/day2-operations-runbooks/README.md) |
| `tests/` | 36 | [Lab 37](../../labs/role-groups/06-change-automation/experiments/validation-fixtures/README.md) |
| `docs/zero-trust/identity/` and `device/` | 12 | [Lab 38](../../labs/role-groups/04-security-trust/experiments/identity-device-assurance/README.md) |
| `applications/internal-iaas-portal/ansible/` | 8 | [Lab 39](../../labs/role-groups/02-cloud-foundation/experiments/k3s-ansible-bootstrap/README.md) |
| `docs/zero-trust/packages/` | 38 | [Lab 40](../../labs/role-groups/04-security-trust/experiments/zero-trust-package-contracts/README.md) |

The copied files are still **reference material**, not independently executable or verified lab builds. File names and counts were compared against the source tree; content-wide security review and hash equivalence for every file have **not** been completed.

## Remaining or partially extracted areas

| Source path | Source files | Reason for retaining original |
|---|---:|---|
| `docs/zero-trust/recovery/` | 88 | Large historical recovery and execution analysis; do not misrepresent as current lab evidence |
| `docs/evidence/zero-trust/` | 52 | Historical evidence and context may include identifiers; requires manual redaction decisions |
| `docs/zero-trust/target-architecture/` | 26 | All 26 source files extracted into [Lab 46](../../labs/role-groups/04-security-trust/experiments/zero-trust-target-architecture/README.md), including three large matrices; no runtime acceptance inferred |
| `applications/internal-iaas-portal/services/user-portal/eclipse/` | 31 | Source manifest attributes major content to separate `Project-Team-Eclipse` team repo. Review reuse rights and preserve attribution before replication |
| `docs/platform/` | 20 | Some contracts imported to Labs 27/30, remainder requires dependency analysis |
| `tools/live-validation/` | 33 | All 33 source files preserved as [Lab 45](../../labs/role-groups/06-change-automation/experiments/remote-readonly-validation/README.md) references, including dangerous installation/scheduling paths; not runnable |
| `tools/local-vm/` | 5 | Host provisioning and VM automation can have side effects |

The counts in this table are **original subtree totals**, not remaining-file counts. A partially extracted subtree can contain both migrated and unmigrated files. Full byte-level migration coverage was not calculated.

## Deletion gate

1. Full independent Git mirrors (all branches/tags, including LFS where applicable), test restoration, and separate GitHub issue/PR/release metadata export.
2. Review every remaining unique code/document and imported-team license/permissions.
3. Scan the destination for credential-like data, internal network endpoints, raw logs and embedded binaries. Static pattern checks run during transfer were limited and not a substitute for a complete scan.
4. Rebuild each lab as independent reproducible units, then test normal, denied, failed, and recovered behavior.
5. Merge and verify in `main` only after review. **This migration does not authorize source repository deletion.**


## Continued source extraction (41–48)

- Team Dandelion: 41 (Restic scenarios), 42 (health triage), 43 (service network design), 47 (repository quality). Historical team logs, screenshots/presentation and environment-specific materials remain in the source repository. It contains planning references for HAProxy/MariaDB/Prometheus, **not a complete ready-to-run HA deployment**.
- `snsd-multicloud-ops`: 44 (OpenStack monitoring IaC/Ansible), 45 (all 33 remote validation files as inert source), 46 (all 26 target architecture files plus KISA control mapping), 48 (19 remaining Restic restore/maintenance source files). Historical Zero Trust evidence and external-team portal content remain in source; all three large matrices are copied into Lab 46.
- Keep source repositories until full Git-mirror restoration and GitHub-only metadata export have been verified. The manifests alone are not backups.


## Last selective extraction: 49–51

- IDP edge WAF and service API contract tests extracted to [Lab 49](../../labs/role-groups/03-platform-delivery/experiments/edge-security-service-contracts/README.md); original third-party Eclipse UI remains source-only pending reuse rights.
- OpenStack provider/network Terraform examples and bounded host/DB checks extracted to [Lab 50](../../labs/role-groups/02-cloud-foundation/experiments/openstack-network-validation/README.md).
- Five host-level VM creation or disk modification scripts extracted as **inert** `.reference.txt` samples in [Lab 51](../../labs/role-groups/02-cloud-foundation/experiments/disposable-lab-host-provisioning/README.md).
- Original architecture decision docs are in [legacy ADR archive](../archive/legacy-adr/README.md), not a current lab acceptance record.
- Historical Zero Trust `recovery/` 88-file and `docs/evidence/zero-trust/` 52-file trees, Dandelion's team logs/screenshots/slides and imported third-party Eclipse portal code are intentionally not bulk-published into a personal lab repository. The original repositories remain the authoritative holdings until independently backed up.
- Role-level integration is [organized](../../labs/role-groups/README.md) but **not runtime verified**, nor is deletion of any original repository authorized.
