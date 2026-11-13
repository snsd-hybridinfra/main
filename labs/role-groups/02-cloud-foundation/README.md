# Cloud Foundations, IaC & Provisioning

AWS·Azure·OpenStack의 가상 주소 계획을 검토하고 배포 전에 대역 중복을 찾습니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 02-cloud-foundation
```

멀티클라우드·OpenStack 네트워크 실험의 Terraform 예제에서 상위 대역과 두 서브넷의 CIDR 리터럴을 읽습니다. 공급자 내 서브넷 포함·중복과 공급자 간 상위 대역 중복을 검사하고, 겹치는 서브넷 입력을 거부합니다. 결과는 `address-plan.json`에 저장합니다.

실습 범위는 예제 주소 계획입니다. 공급자별 초기화·배포는 아래 실험의 절차를 따릅니다.

## 실험

| 실험 | 검증 기록 |
|---|---|
| [AWS & Azure Network IaC Baselines](experiments/multicloud-network-iac/README.md) | 이관 자료 · 개별 재검증 전 |
| [Terraform Security Validation: 공개 SSH 탐지와 수정 재검증](experiments/terraform-security-validation/README.md) | 기존 로컬 검증 기록 |
| [k3s Single-Node Bootstrap via Ansible](experiments/k3s-ansible-bootstrap/README.md) | 이관 자료 · 개별 재검증 전 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [AWS 2-Tier VPC with Ansible](experiments/aws-2tier-vpc/README.md) | 이관 자료 · 개별 재검증 전 |
| [OpenStack Provisioning and Ansible Day-2 Operations](experiments/openstack-ansible-operations/README.md) | 이관 자료 · 개별 재검증 전 |
| [Cloud Network and Access Guardrails](experiments/cloud-network-access-baselines/README.md) | 이관 자료 · 개별 재검증 전 |
| [Cloud Cost & Resource Cleanup Guardrails](experiments/cost-cleanup-guardrails/README.md) | 이관 자료 · 개별 재검증 전 |
| [OpenStack Network IaC & Host Validation](experiments/openstack-network-validation/README.md) | 이관 자료 · 개별 재검증 전 |
| [Disposable Lab VM and Storage Provisioning](experiments/disposable-lab-host-provisioning/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
