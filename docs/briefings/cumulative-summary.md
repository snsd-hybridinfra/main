# 2026년 9~11월 브리핑 누적 핵심 정리

**2026년 11월 2일 (월) 기준 · 대상 09-08~11-02**  
자료 범위와 누락 구간은 [출처 기록](source-register.md)을 따른다. 10월 18일까지의 내용은 기존 저장소를 종합했고, 10월 말 보완 항목은 공식 자료로 확인했다.

## 핵심 판단

현재 학습의 중심은 **네트워크 경로와 장애를 설명하는 능력 → 변경 검증·자동화 → 클라우드 네트워크와 보안 → AI 인프라** 순서로 잡는다. 이것은 브리핑에서 도출한 학습 판단이며 채용시장 통계나 취업 보장이 아니다.

브리핑을 포트폴리오로 바꾸는 단위는 기사 수가 아니라 기술 질문이다. 같은 VPN·관리 장비 이슈가 반복되면 새 랩을 늘리기보다 기존 관리망 분리·취약점 우선순위·복구 랩을 보강한다.

## 1. 네트워크: 장비별 설정에서 경로·정책·장애로

기존 브리핑 정리에서는 BGP/ECMP, Spine-Leaf, EVPN/VXLAN, DCI, 애플리케이션 경로 검증이 연결돼 있다. 10월 30일 컨퍼런스 기록의 Cisco Live 자료도 서로 다른 Fabric의 연결과 변경 전후 검증으로 이어진다. 공식 자료는 [S04·S05](source-register.md)를 참조한다.

학습 질문은 다음 세 가지로 줄인다.

1. Underlay의 IP 도달성이 끊긴 것인지, Overlay의 MAC·IP 경로 또는 VNI 연결이 틀린 것인지 구분할 수 있는가?
2. 같은 세그먼트의 통신 허용과 다른 세그먼트의 거부를 모두 확인했는가?
3. 링크·Spine·경계 노드가 사라졌을 때 경로와 서비스가 각각 어떻게 바뀌는가?

**기존 랩:** [01 BGP/ECMP](../../labs/01-bgp-ecmp/README.md), [02 EVPN/VXLAN](../../labs/02-evpn-vxlan/README.md), [10 Network Digital Twin](../../labs/10-network-digital-twin/README.md).

기존 로컬 Fabric 결과를 상용 ACI·EOS·실제 DCI 검증으로 확대하지 않는다. 다음 단계는 두 Fabric 경계의 VRF·VNI·경로 정책을 설계하고 정상·거부·장애 기대값을 먼저 쓰는 것이다.

## 2. 클라우드: 설치보다 연결·권한·복구

기존 정리의 Hybrid·Private·Sovereign Cloud, IAM/STS, 데이터 복구, Region 간 데이터 경로는 모두 외부 의존성과 책임 경계라는 질문으로 묶인다. 10월 말 OpenStack 네트워킹 자료는 물리 Fabric과 테넌트 라우팅·격리의 연결을 보완한다. 기술 세부 사항은 [컨퍼런스 노트](conference-notes.md)에 정리했다.

| 학습 질문 | 연결 랩 | 기존 결과를 읽을 때의 경계 |
|---|---|---|
| 누가 어떤 역할을 맡아 어떤 요청을 할 수 있는가? | [04 IAM/STS](../../labs/04-iam-sts/README.md) | 합성 정책 평가와 실제 STS 발급·만료는 별도 |
| 백업이 존재하는 것과 복구되는 것은 어떻게 다른가? | [05 Backup & Recovery](../../labs/05-backup-recovery/README.md) | 같은 장비의 로컬 사이트 모델과 실제 재해복구는 별도 |
| 원본·Cache·네트워크 중 어디에서 병목·손상이 발생하는가? | [12 AI Multi-Region Data Path](../../labs/12-ai-multiregion-data-path/README.md) | 로컬 파일 모델과 실제 Region·WAN·제품 성능은 별도 |
| 라우트 광고와 테넌트 격리는 어떤 조건에서 허용되는가? | [01](../../labs/01-bgp-ecmp/README.md)·[02](../../labs/02-evpn-vxlan/README.md) 확장 계획 | OpenStack/OVN·FRR 연동은 이번에 실행하지 않음 |

## 3. 보안: 관리·제어 Plane과 비인간 계정

이전 기록의 F5·NetScaler·원격지원·백업 관리·Workload Identity·Kubernetes Operator·Agent 보안은 권한이 모이는 경계를 보호한다는 문제로 연결된다. 10월 말에는 SD-WAN 제어면 침해와 PAN-OS 관리 인터페이스 위험, SSL VPN 가용성 이슈가 추가됐다. 구체적인 확인 범위는 [후속 정리](latest-updates.md)에 있다.

운영 질문은 **제품·버전 → 기능·설정 → 접근 경로 → 실제 악용 근거 → 조치 책임 → 조치 후 서비스 확인** 순서로 정리한다. 점수 하나나 제품 이름만으로 조치 대상을 확정하지 않는다.

**기존 랩:** [06 AAA/RADIUS](../../labs/06-aaa-radius/README.md), [07 AI Agent Security](../../labs/07-ai-agent-security/README.md), [09 Edge Load Balancer HA](../../labs/09-load-balancer-ha/README.md), [11 Vulnerability Prioritization](../../labs/11-vulnerability-prioritization/README.md), [13 Kubernetes RBAC](../../labs/13-kubernetes-rbac/README.md).

인증 성공, 권한 허용, 망 접근 허용은 각각 다른 판정이다. Agent ID나 ServiceAccount가 있다는 사실만으로 최소 권한과 감사가 완성되지는 않는다. 이 구분을 기존 랩의 허용·거부 증적으로 설명한다.

## 4. 자동화·관측: 명령 실행에서 변경 결과 검증으로

기존 RESTCONF/Python·Digital Twin·Terraform 보안 검증을 하나의 변경 흐름으로 연결한다. Cisco Live의 Network as Code 자료는 코드화된 모델, 사전 검증, 배포, 사후 시험을 구분한다. 아래 흐름은 해당 자료를 참고한 **개인 실습 설계**다.

| 단계 | 남길 결과 | 기존 랩 |
|---|---|---|
| 현재 상태 수집 | CLI/API 값, 수집 시각, 수집 실패 | [03 RESTCONF/Python](../../labs/03-restconf-python/README.md) |
| 기대 상태 정의 | 경로·격리·관리 접근의 허용·거부 표 | [10 Digital Twin](../../labs/10-network-digital-twin/README.md) |
| 변경 전 검사 | 구문 오류와 정책 위반을 구분한 판정 | [14 Terraform Security Validation](../../labs/14-terraform-security-validation/README.md) |
| 변경 후 비교 | 의도한 차이, 예상 밖 차이, 확인 불가 | 기존 랩 확장 계획 |
| 원복·복구 확인 | 이전 상태 재확인과 서비스 시험 | 기존 장애·복구 랩 확장 계획 |

Logs·Metrics·Traces와 AIOps는 관측을 해석하는 학습 주제로 둔다. Digital Twin의 합성 경로 계산 결과를 실제 Telemetry 수집·실시간 장애 탐지 성과로 표현하지 않는다.

## 5. AI 인프라: GPU 외에 데이터 경로와 시설 의존성

기존 브리핑에는 GPU·메모리·고속 Ethernet·RoCE/RDMA·광 연결·전력·냉각·통합 운영 주제가 축적돼 있다. 학습에서는 Scale-up/Scale-out, 혼잡, 데이터 공급, 전력·냉각 장애의 서비스 영향을 나눠 본다.

**기존 랩:** [08 AI DC Network](../../labs/08-ai-dc-network/README.md), [12 AI Multi-Region Data Path](../../labs/12-ai-multiregion-data-path/README.md), [05 Backup & Recovery](../../labs/05-backup-recovery/README.md).

가상 TCP 병목 실습은 처리량·지연을 관측하는 출발점이다. RoCEv2·RDMA·PFC·ECN·상용 GPU Fabric 성능을 검증한 결과는 아니다. 투자금·센터 용량·제품 홍보 수치는 직접 측정한 성능과 분리한다. 데이터센터코리아는 기준일 현재 행사 전이므로 발표 성과 대신 사후에 확인할 질문만 남겼다.

## 6. 커리어·자격증: 넓히기 전에 설명 가능한 깊이

기존 [커리어 로드맵](../career-roadmap.md)의 순서를 유지한다. 네트워크 기본기와 장애 대응을 먼저 설명하고, Python/API로 반복 점검을 줄인 다음 클라우드·보안·AI 인프라로 넓힌다. 자격증의 시험 버전·응시료·일정은 이 문서에서 새로 확인하지 않았다.

면접·포트폴리오에서는 다음 질문에 답할 수 있는 랩을 대표로 고른다.

- 정상 상태에서 기대한 경로와 실제 출력이 일치했는가?
- 장애 또는 금지 요청에서 무엇이 바뀌고 무엇이 유지됐는가?
- 복구 후 다시 같은 검사를 통과했는가?
- 합성 모델·로컬 런타임·실제 운영 중 어디까지 확인했는가?

대표 묶음은 **01·02 네트워크 → 03·10 변경 검증 → 09·11 관리 경계 보안**으로 잡는다. 04·05·13·14는 클라우드·플랫폼 역량의 보완 증거로 연결하고, 07·08·12는 확장 학습으로 둔다.

## 기록의 변화

| 시기 | 저장소에 남은 흐름 | 이번 반영 방식 |
|---|---|---|
| 9월 초~중순 | 데일리 브리핑 시작, 관심 분야·편집 기준 확정 | 전체 정리의 범위와 분류 기준으로 유지 |
| 9월 하순 | Fabric·API·권한·복구·경계 보안의 독립 랩 구성 | 14개 랩의 기술 질문으로 통합 |
| 10월 1~18일 | AIDC 운영·워크로드 권한·취약점·Agent·OT 분리로 확장 | 기존 기록과 증적의 위치를 연결 |
| 10월 말 | SD-WAN 제어면, 관리 인터페이스, VPN, NaC, OpenStack 네트워크 | 새 공식 근거와 후속 실습 계획 추가 |
| 11월 2일 | 이번 누적 정리 기준일 | 일별 원문이 확보됐다는 의미로 사용하지 않음 |

[다음 학습·실습 우선순위](next-actions.md) · [출처와 확보 범위](source-register.md)
