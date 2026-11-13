# 브리핑을 다음 실습으로 바꾸는 순서

**2026년 11월 2일 (월) 기준 · 아래 항목은 모두 계획**

이번 변경은 문서 정리다. 기존 14개 랩의 코드를 실행하거나 새 증적을 만들지 않았다. 반복 주제는 기존 랩을 확장하고, 독립된 기술 질문이 생길 때만 새 랩을 만든다.

## 우선순위

| 순서 | 할 일 | 연결 랩 | 완료 기준 |
|---|---|---|---|
| 1 | Fabric 패킷 경로를 Underlay·Overlay로 나눠 설명 | [01](../../labs/role-groups/01-network-fabric/experiments/bgp-ecmp/README.md)·[02](../../labs/role-groups/01-network-fabric/experiments/evpn-vxlan/README.md) | 정상·격리·단일 장애·복구를 같은 양식으로 설명하고 출력으로 확인 |
| 2 | 변경 전후 상태 비교를 읽기 전용으로 구성 | [03](../../labs/role-groups/06-change-automation/experiments/restconf-python/README.md)·[10](../../labs/role-groups/01-network-fabric/experiments/network-digital-twin/README.md) | 정상·예상 밖 차이·수집 실패를 구분하고 실패 시 성공 판정을 멈춤 |
| 3 | 취약점 영향 조건과 관리 접근 경로를 분리 | [09](../../labs/role-groups/01-network-fabric/experiments/load-balancer-ha/README.md)·[11](../../labs/role-groups/04-security-trust/experiments/vulnerability-prioritization/README.md) | 영향 있음·없음·확인 불가를 구분하고, 악용 근거와 접근 경로를 별도 기록 |
| 4 | 클라우드 역할·실제 권한·복구 확인을 연결 | [04](../../labs/role-groups/04-security-trust/experiments/iam-sts/README.md)·[05](../../labs/role-groups/07-recovery-dr/experiments/backup-recovery/README.md)·[13](../../labs/role-groups/04-security-trust/experiments/kubernetes-rbac/README.md)·[14](../../labs/role-groups/02-cloud-foundation/experiments/terraform-security-validation/README.md) | 합성 판정과 실제 런타임 결과를 구분하며 허용·거부·복구 시험 확보 |
| 5 | AI Fabric·시설 의존성을 학습 질문으로 축소 | [08](../../labs/role-groups/01-network-fabric/experiments/ai-dc-network/README.md)·[12](../../labs/role-groups/01-network-fabric/experiments/ai-multiregion-data-path/README.md)·[10](../../labs/role-groups/01-network-fabric/experiments/network-digital-twin/README.md) | 측정 가능한 병목·경로·의존성 하나를 정하고 장비 없이 확인할 수 없는 범위를 표시 |

## 먼저 만들 작은 결과물

### A. Fabric 경로 설명표

합성 토폴로지의 `출발 세그먼트 → Leaf → Underlay 경로 → 목적 VTEP → 목적 세그먼트`를 기록한다. 같은 세그먼트 허용, 다른 세그먼트 거부, 단일 Spine 장애, 복구 후 상태를 함께 비교한다. 고객사 설정·주소·장비명을 사용하지 않는다.

### B. 변경 검증 보고서

현재 상태 스냅샷과 기대 상태를 입력으로 받아 `일치 / 불일치 / 확인 불가`를 출력한다. API 실패·누락 필드는 통과로 처리하지 않는다. 보고서는 변경 전후 차이와 실패 이유를 남기고, 실제 자동 배포·원복을 구현하지 않았다면 그대로 표시한다.

### C. 취약점 적용 범위 표

합성 자산에 다음 필드를 둔다.

| 필드 | 필요한 이유 |
|---|---|
| 제품·릴리스·기능·설정 조건 | 공지의 영향 범위와 자산 정보를 비교 |
| 관리·제어·사용자 접근 경로 | 노출과 기능 사용 여부를 분리 |
| 악용 근거·출처·확인일 | 공식 영향 공지·실제 악용·KEV를 혼동하지 않기 위해 필요 |
| 정보 누락·확인 담당 | 확인 불가를 안전 판정으로 바꾸지 않기 위해 필요 |
| 조치·승인·검증·원복 기준 | 패치 실행과 작업 완료를 구분 |

KeyDrift·PAN-OS·ASA/FTD 항목은 이 구조에 맞춰 정리한 뒤 11번 랩에 통합할지 판단한다. 새 점수나 패치 성공 결과를 먼저 적지 않는다.

## 공부 기록의 최소 단위

한 번에 기사 하나, 기술 질문 하나, 랩 변경 하나를 다룬다. `문제 → 기대값 → 실제 출력 → 장애·거부 → 복구 → 한계`가 이어지는 결과를 남긴다. 자격증 공부에서 배운 BGP·스위칭·AAA·가용성 개념을 이 출력과 연결한다.

새 컨퍼런스 자료는 [컨퍼런스 노트](conference-notes.md)의 질문으로 선별한다. 제품 이름을 더 모으는 것보다 기존 랩의 설명·증적·실패 처리 수준을 높이는 데 우선 반영한다.
