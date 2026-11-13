# Labs 41–48: Source Migration Register

**Recorded:** 2026-11-12 KST  
**Destination:** `snsd-hybridinfra/main` draft PR #3, `chore/portfolio-structure-2026-11`  
**State:** `SOURCE_EXTRACTED / NOT_REVALIDATED`

| Lab | Source | Original files selected | Treatment |
|---|---|---:|---|
| [41 Dandelion Restic Recovery](../../labs/role-groups/07-recovery-dr/experiments/dandelion-restic-recovery/README.md) | Team Dandelion | 5 | 다중 서비스 Restic 복구 시나리오; no runtime validation |
| [42 Dandelion Health Triage](../../labs/role-groups/05-observability-sre/experiments/dandelion-health-triage/README.md) | Team Dandelion | 9 | Web·DB·Proxy 상태 점검·자동복구 위험 분리; no runtime validation |
| [43 Dandelion Service Topology](../../labs/role-groups/01-network-fabric/experiments/dandelion-service-topology/README.md) | Team Dandelion | 8 | OpenStack·HAProxy·WordPress·MariaDB 설계; no runtime validation |
| [44 OpenStack Observability Deployment](../../labs/role-groups/05-observability-sre/experiments/openstack-observability-deployment/README.md) | snsd-multicloud-ops | 37 | Terraform·Ansible·mTLS 모니터링 배포 소스; no runtime validation |
| [45 Remote Read-Only Validation](../../labs/role-groups/06-change-automation/experiments/remote-readonly-validation/README.md) | snsd-multicloud-ops | 33 | EVE-NG·라우터·OpenStack 검증 및 증적; no runtime validation |
| [46 Zero Trust Target Architecture](../../labs/role-groups/04-security-trust/experiments/zero-trust-target-architecture/README.md) | snsd-multicloud-ops | 23 | 아키텍처·수용 기준·의존성; no runtime validation |
| [47 Repository Quality Gates](../../labs/role-groups/06-change-automation/experiments/repository-quality-gates/README.md) | Team Dandelion | 8 | CI 검증·리뷰·문서 자동화; no runtime validation |
| [48 Restic Restore & Maintenance](../../labs/role-groups/07-recovery-dr/experiments/restic-restore-maintenance/README.md) | snsd-multicloud-ops | 19 | 복원·유지보수·systemd 타이머; no runtime validation |

## Common constraints

- `snsd-hybridinfra/dandelion-cloud-automation` source commit: `22a21c02973e696a9a07c91da3bc2ea033881ea6`. Team provenance preserved; no source team assets may be relabeled as individual authorship.
- `snsd-hybridinfra/snsd-multicloud-ops` source commit: `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
- The 8 labs preserve **142 selected source file copies**, not complete repos. Executable maintenance, remote installer, auto-restore and CI write routines are not activated. Some are renamed `.reference.txt` and a few example addresses/passwords generalized.
- Some original references describe intended HAProxy/Prometheus/WordPress integration; these are plans, not verified failover results or importable HAProxy config.
- Only a limited source-pattern check was performed before writing. No runtime execution, comprehensive secret scan, vulnerability scan or Git-mirror backup has been performed.

## Remaining or deliberately omitted

- Team Dandelion: team meeting notes, work logs, screenshots, PPTX and other original contributors' materials. These are retained in the source repo.
- Multicloud: three large architecture matrix YAML files, historical Zero Trust evidence/recovery histories, external-team portal source, unselected application/tool files. Retain original.
- Original repository branches, tags, issues, PRs, releases, LFS or other data are **not preserved** in the extracted labs or file manifests.
