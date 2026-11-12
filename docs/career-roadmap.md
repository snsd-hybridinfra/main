# 네트워크 기반 인프라 커리어 로드맵

「IT·보안 데일리 브리핑」에서 반복된 기술 흐름을 학습 순서로 정리한 문서입니다. 산업 전망은 진로 선택의 참고 자료이며, 이 단계들이 채용 수요나 취업 결과를 보장한다는 뜻은 아닙니다.

| 단계 | 학습 초점 | 포트폴리오에서 확인할 결과 |
|---|---|---|
| 1. 네트워크 기반 | CCNP 수준의 OSPF, BGP, 스위칭, 이중화, QoS, AAA | 정상·장애 경로를 설명하고 재현 |
| 2. 데이터센터 네트워크 | Spine-Leaf, ECMP, BGP Fabric, EVPN/VXLAN | 토폴로지와 경로 수렴·분리 증적 |
| 3. 자동화·Assurance | Python, RESTCONF/NETCONF, YANG, Telemetry, Digital Twin | CLI/API 대조, 경로·의도 검증, 반복 점검 코드 |
| 4. 클라우드·플랫폼 | Linux, OpenStack/AWS 네트워크, IAM, Terraform, Kubernetes | 최소 권한·네트워크·복구 실습 |
| 5. 보안 운영 | AAA, 관리 Plane, KEV, 취약점 우선순위, 감사 | 허용·거부와 자산 기반 조치 순서를 증적으로 설명 |
| 6. AI 인프라 | GPU 클러스터 네트워크, RoCEv2, 혼잡 제어, 광 연결, 관측 | 개념 정리 후 재현 가능한 범위의 실험 |

보안은 각 단계에 함께 적용합니다. 우선순위는 자격증명 관리와 최소 권한 → 네트워크 분리 → 취약점·공급망 관리 → 관측·감사 → Agent 보안입니다.

## 실제 경험으로 바꾸는 기준

자격증이나 뉴스 요약만 나열하지 않습니다. 각 단계에서 다음을 설명할 수 있어야 합니다.

1. 어떤 운영 문제가 있었는가?
2. 어떤 대안을 비교했고 왜 이 구성을 선택했는가?
3. 장애·거부·복구를 어떻게 시험했는가?
4. 실제 출력과 예상이 달랐던 부분은 무엇인가?
5. 결과를 대표 프로젝트에 적용할 수 있는 범위와 한계는 무엇인가?

현재 단일 실습 저장소는 [main](https://github.com/snsd-hybridinfra/main)입니다. [15 AWS VPC](../labs/15-aws-2tier-vpc/README.md), [16 OpenStack Ansible](../labs/16-openstack-ansible-operations/README.md), [17 Network & Access Guardrails](../labs/17-cloud-network-access-baselines/README.md)는 이전 실험 저장소에서 이관했으나 재검증 전입니다. 기술 영역별 랩이 독립적으로 검증된 뒤에만 통합 프로젝트를 기획합니다. [이관 대장](migration-register.md)에서 원본 출처와 미이관 범위를 확인할 수 있습니다.
