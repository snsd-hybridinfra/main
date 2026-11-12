# Cloud Foundations, IaC & Provisioning

**Primary role group** `02-cloud-foundation` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
AWS·Azure·OpenStack의 네트워크/VM 자원을 안전하게 선언·검증·폐기

## 단일 실습 흐름
Terraform baseline(14,24,50) → AWS/OpenStack Ansible(15,16) → 정책/비용 게이트(17,23) → k3s·VM 부트스트랩(39,51)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 14 | [14-terraform-security-validation](../../14-terraform-security-validation/README.md) | 기존 로컬 검증 기록 |
| 15 | [15-aws-2tier-vpc](../../15-aws-2tier-vpc/README.md) | 이관·재검증 대기 |
| 16 | [16-openstack-ansible-operations](../../16-openstack-ansible-operations/README.md) | 이관·재검증 대기 |
| 17 | [17-cloud-network-access-baselines](../../17-cloud-network-access-baselines/README.md) | 이관·재검증 대기 |
| 23 | [23-cost-cleanup-guardrails](../../23-cost-cleanup-guardrails/README.md) | 이관·재검증 대기 |
| 24 | [24-multicloud-network-iac](../../24-multicloud-network-iac/README.md) | 이관·재검증 대기 |
| 39 | [39-k3s-ansible-bootstrap](../../39-k3s-ansible-bootstrap/README.md) | 이관·재검증 대기 |
| 50 | [50-openstack-network-validation](../../50-openstack-network-validation/README.md) | 이관·재검증 대기 |
| 51 | [51-disposable-lab-host-provisioning](../../51-disposable-lab-host-provisioning/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 14+15+24+50: 공통 네트워크 의도 스키마와 공급자별 Terraform/Ansible 어댑터
- 16+39+51: VM 생성과 서비스 설치 작업을 별도 승인 단계로 분리

## 역할군 공통 인터페이스

- **Input:** provider-neutral CIDR/route/SG policy, synthetic inventory, disposable account
- **Output:** static Terraform plan, Ansible syntax/changed report, provider validation matrix
- **Mandatory gate:** 잘못된 CIDR, 공개 노출, 정책 누락, 비용 초과, 공급자 오류, destroy 거부

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
