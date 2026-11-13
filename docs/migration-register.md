# Experiment Repository → Main Labs Migration Register

**Recorded:** 2026-11-11 (KST)  
**Destination:** `snsd-hybridinfra/main` (review branch `chore/portfolio-structure-2026-11`)  
**State:** `EXTRACTED / AWAITING_REVALIDATION / SOURCES_RETAINED`

The original experiment IDs below are retained for provenance. The links point to the current [seven-lab structure](../README.md).

The old projects are sources of reusable **labs**, not automatically completed integration projects. Thirty-seven source-derived labs are registered: 15 through 51, including thirty-one from snsd-multicloud-ops, five from Team Dandelion, and one from the private AWS test repo. These are extraction units, not verified runnable projects. The original repositories have **not** been deleted or archived. This register does not constitute a full backup.

| Source repository | Source commit SHA | Destination | Source files selected | Not imported |
|---|---|---|---:|---|
| [test](https://github.com/snsd-hybridinfra/test) (private) | `6147e9114e79aed5034be2bcd9ee1f6e7b4a695f` | [Lab 15](../labs/role-groups/02-cloud-foundation/experiments/aws-2tier-vpc/README.md) | 14 | Duplicated nested tree, generated example outputs, source commit history |
| [dandelion-cloud-automation](https://github.com/snsd-hybridinfra/dandelion-cloud-automation) | `22a21c02973e696a9a07c91da3bc2ea033881ea6` | [Lab 16](../labs/role-groups/02-cloud-foundation/experiments/openstack-ansible-operations/README.md) | 6 | Team work logs, diagrams, screenshots, presentations, risky auto-recovery scripts, most documents, history |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | `fd5b2286a68da180fd51ecb247516c960cc7d4ef` | [Lab 17](../labs/role-groups/02-cloud-foundation/experiments/cloud-network-access-baselines/README.md) | 14 | Original portal and broader platform |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 18](../labs/role-groups/05-observability-sre/experiments/sanitized-observability/README.md) | 4 | Full monitoring system, real runtime evidence |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 19](../labs/role-groups/05-observability-sre/experiments/metric-anomaly-scoring/README.md) | 7 | Trained ML system; not present in original scripts |
| [snsd-multicloud-ops](https://github.com/snsd-hybridinfra/snsd-multicloud-ops) | same SHA | [Lab 20](../labs/role-groups/07-recovery-dr/experiments/postgres-restic-verification/README.md) | 8 | Prune/retention, full restore, systemd schedule, runtime evidence |

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

## Additional source extraction (2026-11-12)

| Lab | Scope | Validation |
|---|---|---|
| [21 Change Automation & Approval](../labs/role-groups/06-change-automation/experiments/automation-approval/README.md) | 승인·위험 분류 | `NOT_REVALIDATED` |
| [22 Continuous Verification](../labs/role-groups/06-change-automation/experiments/continuous-verification/README.md) | 증적 신선도·회귀·반복성 | `NOT_REVALIDATED` |
| [23 Cost & Cleanup Guardrails](../labs/role-groups/02-cloud-foundation/experiments/cost-cleanup-guardrails/README.md) | 비용·정리 정책 | `NOT_REVALIDATED` |
| [24 Multi-cloud Network IaC](../labs/role-groups/02-cloud-foundation/experiments/multicloud-network-iac/README.md) | AWS·Azure Terraform | `NOT_REVALIDATED` |
| [25 Container Supply Chain](../labs/role-groups/03-platform-delivery/experiments/container-supply-chain/README.md) | 컨테이너 빌드 공급망 | `NOT_REVALIDATED` |
| [26 Service Observability](../labs/role-groups/05-observability-sre/experiments/service-observability/README.md) | Prometheus·Blackbox·Nginx | `NOT_REVALIDATED` |
| [27 Self-Service Request API](../labs/role-groups/03-platform-delivery/experiments/self-service-request-api/README.md) | 신청 API·카탈로그 | `NOT_REVALIDATED` |
| [28 Approval & Grant Lifecycle](../labs/role-groups/03-platform-delivery/experiments/approval-grant-lifecycle/README.md) | 승인·권한·만료 | `NOT_REVALIDATED` |
| [29 Terraform Runner & Blueprints](../labs/role-groups/03-platform-delivery/experiments/terraform-runner-blueprints/README.md) | OpenStack 상품·실행기 | `NOT_REVALIDATED` |
| [30 Agent & Data Contracts](../labs/role-groups/03-platform-delivery/experiments/agent-data-contracts/README.md) | Agent·NAS·금융 SaaS 경계 | `NOT_REVALIDATED` |
| [31 Kubernetes GitOps](../labs/role-groups/03-platform-delivery/experiments/kubernetes-gitops/README.md) | 63개 매니페스트 | `NOT_REVALIDATED` |
| [32 Zero Trust Baselines](../labs/role-groups/04-security-trust/experiments/security-baselines/README.md) | SSH·서비스·데이터 정책 | `NOT_REVALIDATED` |
| [33 EVE-NG Assurance](../labs/role-groups/01-network-fabric/experiments/eve-network-assurance/README.md) | 라우팅·읽기 전용 검증 | `NOT_REVALIDATED` |

### Source inventory is not a complete backup

- [Source file manifest](migration/snsd-multicloud-ops-source-file-manifest.tsv): 1,252 original source `main` branch paths, Git blob SHAs and byte sizes. **No file bytes, history, other branches, issues or PRs are preserved by this manifest itself.**
- Source packages, Terraform modules, and all 63 original IDP Kubernetes manifests have been selectively extracted. The complete database, generic runbooks and source test trees now have extracted reference copies, but **large amounts of imported-team portal code, Zero Trust recovery/evidence history, target architecture, ADRs, and tool-specific assets remain in the original**.
- **No original repository deletion/archival** occurred. A full independent Git mirror and GitHub metadata export must be verified before considering deletion.

## Continued extraction: Labs 34–40 (2026-11-12)

| Lab | Source scope | Copied source files | Limitation |
|---|---|---:|---|
| [34 PostgreSQL Schema & Migrations](../labs/role-groups/03-platform-delivery/experiments/postgres-schema-migrations/README.md) | DB 스키마·Alembic·권한 검증 | 26 | reference only / not revalidated |
| [35 Portal UI Contracts](../labs/role-groups/03-platform-delivery/experiments/portal-ui-contracts/README.md) | 관리자·사용자 UI 기본 셸, 외부 팀 UI 제외 | 10 | reference only / not revalidated |
| [36 Day-2 Operations Runbooks](../labs/role-groups/06-change-automation/experiments/day2-operations-runbooks/README.md) | 운영·배포·장애·복구 절차 | 40 | reference only / not revalidated |
| [37 Validation Fixtures](../labs/role-groups/06-change-automation/experiments/validation-fixtures/README.md) | 테스트·합성 데이터·거부 케이스 | 36 | reference only / not revalidated |
| [38 Identity & Device Assurance](../labs/role-groups/04-security-trust/experiments/identity-device-assurance/README.md) | 주체·역할·기기 신뢰 정책 | 12 | reference only / not revalidated |
| [39 k3s Ansible Bootstrap](../labs/role-groups/02-cloud-foundation/experiments/k3s-ansible-bootstrap/README.md) | 단일 노드 k3s Ansible 구성 | 8 | reference only / not revalidated |
| [40 Zero Trust Package Contracts](../labs/role-groups/04-security-trust/experiments/zero-trust-package-contracts/README.md) | 보안 패키지·검증·롤백 계약 | 38 | reference only / not revalidated |

The original `snsd-multicloud-ops` source had **1,252 tracked file entries** on the pinned `main` commit. This register tracks selected file transfers, not a byte-for-byte migration of the full repository or its history. For remaining unique source trees, see [remaining-source-areas.md](migration/remaining-source-areas.md).


## Continued extraction: Labs 41–48 (2026-11-12)

The eight new reference labs and detailed migration decisions are recorded in [new-labs-41-48.md](migration/new-labs-41-48.md). Team Dandelion's full `main` source tree has been indexed separately in [dandelion-source-file-manifest.tsv](migration/dandelion-source-file-manifest.tsv): 161 file paths, SHA and sizes **only, not a reconstructible backup**.

**Risk boundary:** old automatic repair scripts, network installers, systemd timers and CI write workflows are stored as inert references only. The original source code/data, issue/PR/team attribution and binary assets still require a separate verified backup before deletion.


## Final reusable-source extraction and role consolidation (2026-11-12)

- [Lab 49](../labs/role-groups/03-platform-delivery/experiments/edge-security-service-contracts/README.md): Edge Nginx/ModSecurity source, original interface contracts and missing IDP frontend/integration/security tests.
- [Lab 50](../labs/role-groups/02-cloud-foundation/experiments/openstack-network-validation/README.md): OpenStack Terraform provider/network examples, bastion/DNS and synthetic DB/backup Ansible checks.
- [Lab 51](../labs/role-groups/02-cloud-foundation/experiments/disposable-lab-host-provisioning/README.md): Five VM/host/storage provisioner scripts as inert reference files.
- Source additions to existing Labs 15, 16, 17, 27–29, 41, 43, 46: synthetic AWS output, Dandelion Runbook/backup scripts, K8s policy examples, API Docker build files, full 26/26 Zero Trust architecture files and KISA mapping.
- 27 cross-cutting ADR documents are [archived](archive/legacy-adr/README.md) apart from lab experiments.
- 3 full source metadata inventories: [AWS test](migration/test-source-file-manifest.tsv) 41 paths, [Dandelion](migration/dandelion-source-file-manifest.tsv) 161 paths, [multicloud](migration/snsd-multicloud-ops-source-file-manifest.tsv) 1,252 paths. **These are not reconstructible Git backups.**
- [51 labs belong to 7 mutually exclusive roles](../labs/role-groups/README.md). Their integration contract is [here](lab-interface-contract.md), and the concrete overlap/merge criteria are [here](role-consolidation-plan.md). Role ownership is verified as complete; runtime integration remains untested.
