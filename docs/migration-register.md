# Experiment Repository → Main Labs Migration Register

**Recorded:** 2026-11-11 (KST)  
**Destination:** `snsd-hybridinfra/main` (review branch `chore/portfolio-structure-2026-11`)  
**State:** `EXTRACTED / AWAITING_REVALIDATION / SOURCES_RETAINED`

The old projects are sources of reusable **labs**, not automatically completed integration projects. Six standalone labs are now registered: 15 through 20, including four derived from the former multicloud repository. The original repositories have **not** been deleted or archived. This register does not constitute a full backup.

| Source repository | Source commit SHA | Destination | Source files selected | Not imported |
|---|---|---|---:|---|
| [test](https://github.com/snsd-hybridinfra/test) (private) | `6147e9114e79aed5034be2bcd9ee1f6e7b4a695f` | [Lab 15](../labs/15-aws-2tier-vpc/README.md) | 14 | Duplicated nested tree, generated example outputs, source commit history |
| [dandelion-cloud-automation](https://github.com/snsd-hybridinfra/dandelion-cloud-automation) | `22a21c02973e696a9a07c91da3bc2ea033881ea6` | [Lab 16](../labs/16-openstack-ansible-operations/README.md) | 6 | Team work logs, diagrams, screenshots, presentations, risky auto-recovery scripts, most documents, history |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | `fd5b2286a68da180fd51ecb247516c960cc7d4ef` | [Lab 17](../labs/17-cloud-network-access-baselines/README.md) | 14 | Original portal and broader platform |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 18](../labs/18-sanitized-observability/README.md) | 4 | Full monitoring system, real runtime evidence |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 19](../labs/19-metric-anomaly-scoring/README.md) | 7 | Trained ML system; not present in original scripts |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 20](../labs/20-postgres-restic-verification/README.md) | 8 | Prune/retention, full restore, systemd schedule, runtime evidence |

## Validation and deletion gate

1. Merge the reviewed destination PR and confirm every lab file and source attribution is present on `main`.
2. Obtain **full independent mirror backups** of all three original Git repositories, including branches and tags (for example, `git clone --mirror`). Check the mirror with `git fsck` and keep it outside the repositories being deleted.
3. Separately export needed GitHub-only metadata: Issues, PR discussion, release assets, project discussions, team attribution and settings. A Git mirror alone does not preserve all GitHub metadata.
4. Scan migrated labs for credentials, private endpoints and unredacted personal/workplace data. Rotate any exposed secrets in the source history if necessary.
5. Check independent lab syntax, dependency versions and a disposable environment normal/negative/recovery run. Do not claim the original project's runtime results apply to the new labs.
6. Review excluded unique files, especially the team project and large IDP repository, then either extract more reusable knowledge into labs or document an explicit intentional omission.
7. Only then delete original repositories through GitHub repository settings with the appropriate admin permission. **Deletion is not part of this migration PR.**

## Long-term project rule

Build and validate independent labs first. Only after multiple labs have stable inputs, outputs, tests and evidence should they be assembled into an IDC/network/cloud/resilience project. New integrated projects must have separate acceptance evidence.

## Further extraction candidates (not yet migrated)

- Change-control automation: `tools/automation/` + its policy/catalog dependencies; must isolate from any remote action execution.
- Evidence freshness/regression: `tools/continuous_verification/` + referenced policies/history; too tightly coupled to copy wholesale.
- Cost/cleanup guardrails: `cost-governance/`; source is mostly templates and decision matrices, requiring a real evaluator and fixtures.
- Container supply chain: `applications/internal-iaas-portal/supply-chain/` + tests; not a standalone CI proof and needs careful security review.
- Portal and lifecycle: `applications/internal-iaas-portal/services/` and tests; extract by service boundary rather than a monolith.

**No repository deletion until all unique material, collaboration history, and GitHub-only metadata are independently backed up and reviewed.**
