# Experiment Repository → Main Labs Migration Register

**Recorded:** 2026-11-11 (KST)  
**Destination:** `snsd-hybridinfra/main` (review branch `chore/portfolio-structure-2026-11`)  
**State:** `EXTRACTED / AWAITING_REVALIDATION / SOURCES_RETAINED`

The old projects are sources of reusable **labs**, not automatically completed integration projects. Twenty-six source-derived labs are registered: 15 through 40, including twenty-four derived from the former multicloud repository. These are extraction units, not verified runnable projects. The original repositories have **not** been deleted or archived. This register does not constitute a full backup.

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

## Additional source extraction (2026-11-12)

| Lab | Scope | Validation |
|---|---|---|
| [21 Change Automation & Approval](../labs/21-automation-approval/README.md) | 승인·위험 분류 | `NOT_REVALIDATED` |
| [22 Continuous Verification](../labs/22-continuous-verification/README.md) | 증적 신선도·회귀·반복성 | `NOT_REVALIDATED` |
| [23 Cost & Cleanup Guardrails](../labs/23-cost-cleanup-guardrails/README.md) | 비용·정리 정책 | `NOT_REVALIDATED` |
| [24 Multi-cloud Network IaC](../labs/24-multicloud-network-iac/README.md) | AWS·Azure Terraform | `NOT_REVALIDATED` |
| [25 Container Supply Chain](../labs/25-container-supply-chain/README.md) | 컨테이너 빌드 공급망 | `NOT_REVALIDATED` |
| [26 Service Observability](../labs/26-service-observability/README.md) | Prometheus·Blackbox·Nginx | `NOT_REVALIDATED` |
| [27 Self-Service Request API](../labs/27-self-service-request-api/README.md) | 신청 API·카탈로그 | `NOT_REVALIDATED` |
| [28 Approval & Grant Lifecycle](../labs/28-approval-grant-lifecycle/README.md) | 승인·권한·만료 | `NOT_REVALIDATED` |
| [29 Terraform Runner & Blueprints](../labs/29-terraform-runner-blueprints/README.md) | OpenStack 상품·실행기 | `NOT_REVALIDATED` |
| [30 Agent & Data Contracts](../labs/30-agent-data-contracts/README.md) | Agent·NAS·금융 SaaS 경계 | `NOT_REVALIDATED` |
| [31 Kubernetes GitOps](../labs/31-kubernetes-gitops/README.md) | 63개 매니페스트 | `NOT_REVALIDATED` |
| [32 Zero Trust Baselines](../labs/32-security-baselines/README.md) | SSH·서비스·데이터 정책 | `NOT_REVALIDATED` |
| [33 EVE-NG Assurance](../labs/33-eve-network-assurance/README.md) | 라우팅·읽기 전용 검증 | `NOT_REVALIDATED` |

### Source inventory is not a complete backup

- [Source file manifest](migration/snsd-multicloud-ops-source-file-manifest.tsv): 1,252 original source `main` branch paths, Git blob SHAs and byte sizes. **No file bytes, history, other branches, issues or PRs are preserved by this manifest itself.**
- Source packages, Terraform modules, and all 63 original IDP Kubernetes manifests have been selectively extracted. The complete database, generic runbooks and source test trees now have extracted reference copies, but **large amounts of imported-team portal code, Zero Trust recovery/evidence history, target architecture, ADRs, and tool-specific assets remain in the original**.
- **No original repository deletion/archival** occurred. A full independent Git mirror and GitHub metadata export must be verified before considering deletion.

## Continued extraction: Labs 34–40 (2026-11-12)

| Lab | Source scope | Copied source files | Limitation |
|---|---|---:|---|
| [34 PostgreSQL Schema & Migrations](../labs/34-postgres-schema-migrations/README.md) | DB 스키마·Alembic·권한 검증 | 26 | reference only / not revalidated |
| [35 Portal UI Contracts](../labs/35-portal-ui-contracts/README.md) | 관리자·사용자 UI 기본 셸, 외부 팀 UI 제외 | 10 | reference only / not revalidated |
| [36 Day-2 Operations Runbooks](../labs/36-day2-operations-runbooks/README.md) | 운영·배포·장애·복구 절차 | 40 | reference only / not revalidated |
| [37 Validation Fixtures](../labs/37-validation-fixtures/README.md) | 테스트·합성 데이터·거부 케이스 | 36 | reference only / not revalidated |
| [38 Identity & Device Assurance](../labs/38-identity-device-assurance/README.md) | 주체·역할·기기 신뢰 정책 | 12 | reference only / not revalidated |
| [39 k3s Ansible Bootstrap](../labs/39-k3s-ansible-bootstrap/README.md) | 단일 노드 k3s Ansible 구성 | 8 | reference only / not revalidated |
| [40 Zero Trust Package Contracts](../labs/40-zero-trust-package-contracts/README.md) | 보안 패키지·검증·롤백 계약 | 38 | reference only / not revalidated |

The original `snsd-multicloud-ops` source had **1,252 tracked file entries** on the pinned `main` commit. This register tracks selected file transfers, not a byte-for-byte migration of the full repository or its history. For remaining unique source trees, see [remaining-source-areas.md](migration/remaining-source-areas.md).
