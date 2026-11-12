# Remaining Unique Source Areas: snsd-multicloud-ops

**Observed:** 2026-11-12 (KST)  
**Pinned source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`  
**Destination:** `snsd-hybridinfra/main` draft PR #3, 40 lab directories

The source has **1,252 tracked files** on its `main` branch. The extracted labs are **not a byte-identical replacement** and do **not** include Git commit history, other branches/tags, issues, pull requests, releases or external assets.

## Subtrees with full source-file copies in Labs 34–40

| Original subtree | Files | Destination |
|---|---:|---|
| `applications/internal-iaas-portal/database/` | 26 | [Lab 34](../../labs/34-postgres-schema-migrations/README.md) |
| `docs/runbooks/` | 40 | [Lab 36](../../labs/36-day2-operations-runbooks/README.md) |
| `tests/` | 36 | [Lab 37](../../labs/37-validation-fixtures/README.md) |
| `docs/zero-trust/identity/` and `device/` | 12 | [Lab 38](../../labs/38-identity-device-assurance/README.md) |
| `applications/internal-iaas-portal/ansible/` | 8 | [Lab 39](../../labs/39-k3s-ansible-bootstrap/README.md) |
| `docs/zero-trust/packages/` | 38 | [Lab 40](../../labs/40-zero-trust-package-contracts/README.md) |

The copied files are still **reference material**, not independently executable or verified lab builds. File names and counts were compared against the source tree; content-wide security review and hash equivalence for every file have **not** been completed.

## Remaining or partially extracted areas

| Source path | Source files | Reason for retaining original |
|---|---:|---|
| `docs/zero-trust/recovery/` | 88 | Large historical recovery and execution analysis; do not misrepresent as current lab evidence |
| `docs/evidence/zero-trust/` | 52 | Historical evidence and context may include identifiers; requires manual redaction decisions |
| `docs/zero-trust/target-architecture/` | 26 | Significant architecture/traceability material; only selected policies imported earlier |
| `applications/internal-iaas-portal/services/user-portal/eclipse/` | 31 | Source manifest attributes major content to separate `Project-Team-Eclipse` team repo. Review reuse rights and preserve attribution before replication |
| `docs/platform/` | 20 | Some contracts imported to Labs 27/30, remainder requires dependency analysis |
| `tools/live-validation/` | 33 | Some validators imported to Lab 33; remote/scheduled variants should not be executed without review |
| `tools/local-vm/` | 5 | Host provisioning and VM automation can have side effects |

The counts in this table are **original subtree totals**, not remaining-file counts. A partially extracted subtree can contain both migrated and unmigrated files. Full byte-level migration coverage was not calculated.

## Deletion gate

1. Full independent Git mirrors (all branches/tags, including LFS where applicable), test restoration, and separate GitHub issue/PR/release metadata export.
2. Review every remaining unique code/document and imported-team license/permissions.
3. Scan the destination for credential-like data, internal network endpoints, raw logs and embedded binaries. Static pattern checks run during transfer were limited and not a substitute for a complete scan.
4. Rebuild each lab as independent reproducible units, then test normal, denied, failed, and recovered behavior.
5. Merge and verify in `main` only after review. **This migration does not authorize source repository deletion.**
