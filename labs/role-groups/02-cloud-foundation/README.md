# Cloud Foundations, IaC & Provisioning

AWS·Azure·OpenStack의 가상 주소 계획을 검토하고 배포 전에 대역 중복을 찾습니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 02-cloud-foundation
```

Lab 24·50의 Terraform 예제에서 상위 대역과 두 서브넷의 CIDR 리터럴을 읽습니다. 공급자 내 서브넷 포함·중복과 공급자 간 상위 대역 중복을 검사하고, 겹치는 서브넷 입력을 거부합니다. 결과는 `address-plan.json`에 저장합니다.

실습 범위는 예제 주소 계획입니다. 공급자별 초기화·배포는 아래 번호 랩의 절차를 따릅니다.

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 14 | [14-terraform-security-validation](../../14-terraform-security-validation/README.md) | 기존 로컬 증적 |
| 15 | [15-aws-2tier-vpc](../../15-aws-2tier-vpc/README.md) | 이관 참고 |
| 16 | [16-openstack-ansible-operations](../../16-openstack-ansible-operations/README.md) | 이관 참고 |
| 17 | [17-cloud-network-access-baselines](../../17-cloud-network-access-baselines/README.md) | 이관 참고 |
| 23 | [23-cost-cleanup-guardrails](../../23-cost-cleanup-guardrails/README.md) | 이관 참고 |
| 24 | [24-multicloud-network-iac](../../24-multicloud-network-iac/README.md) | 이관 참고 |
| 39 | [39-k3s-ansible-bootstrap](../../39-k3s-ansible-bootstrap/README.md) | 이관 참고 |
| 50 | [50-openstack-network-validation](../../50-openstack-network-validation/README.md) | 이관 참고 |
| 51 | [51-disposable-lab-host-provisioning](../../51-disposable-lab-host-provisioning/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
