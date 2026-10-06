# 실습 로드맵

각 주제를 선택한 뉴스 원문, 내가 도출한 질문, 실제 증적과 한계는 [뉴스 → 기술 실습 기록](news-to-labs.md)에 있습니다.

상태 표기는 `계획`, `설계`, `로컬 검증`, `런타임 검증`을 사용합니다. 현재 14개 실습 모두 컨테이너·코드·합성 모델 또는 임시 로컬 클러스터에서 **로컬 검증** 상태입니다. 실제 운영 환경에서 검증한 실습은 없습니다.

| 순서 | 주제 | 직접 확인할 질문 | 남길 증적 |
|---|---|---|---|
| 1 | [BGP/ECMP Spine-Leaf](../labs/01-bgp-ecmp/README.md) — 로컬 검증 | 링크 또는 Spine 장애 후 경로가 수렴하고 통신이 유지되는가? | [설정과 실행 출력](../labs/01-bgp-ecmp/evidence/2026-09-29.txt), 장애 전후 경로·ping |
| 2 | [EVPN/VXLAN](../labs/02-evpn-vxlan/README.md) — 로컬 검증 | 분리된 세그먼트의 허용·거부 통신이 의도대로 동작하는가? | [BGP EVPN·VNI·FDB 및 ping 출력](../labs/02-evpn-vxlan/evidence/2026-09-29.txt) |
| 3 | [RESTCONF/Python](../labs/03-restconf-python/README.md) — 로컬 검증 | API 조회 결과가 장비 CLI 상태와 일치하고 인증 실패 시 비교를 멈추는가? | [합성 인터페이스 3개 일치·불일치 0·HTTP 401 거부](../labs/03-restconf-python/evidence/2026-09-29.json); 실제 장비 대기 |
| 4 | [IAM/STS](../labs/04-iam-sts/README.md) — 로컬 검증 | 신뢰 관계·역할·세션 정책·명시적 거부로 Workload Identity 행동 범위를 줄일 수 있는가? | [합성 정책 판정 7/7 일치](../labs/04-iam-sts/evidence/2026-09-28.json); AWS/Azure 발급·만료·Resource Lock은 미검증 |
| 5 | [백업·복구](../labs/05-backup-recovery/README.md) — 로컬 검증 | 합성 서비스를 복원하거나 재구축하는 데 얼마나 걸리는가? | [RTO 1.627초·손실 2건](../labs/05-backup-recovery/evidence/2026-09-22.json) |
| 6 | [AAA/RADIUS](../labs/06-aaa-radius/README.md) — 로컬 검증 | 등록된 사용자만 RADIUS 인증을 통과하는가? | [Access-Accept 1건·Access-Reject 2건](../labs/06-aaa-radius/evidence/2026-09-22.txt) |
| 7 | [AI Agent Security](../labs/07-ai-agent-security/README.md) — 로컬 검증 | 도구의 권한·통신·예산·합성 승인 경계가 지켜지는가? | [결정적 게이트 실행 결과](../labs/07-ai-agent-security/evidence/2026-09-22.json); 실제 Agent 런타임 대기 |
| 8 | [AI DC Network](../labs/08-ai-dc-network/README.md) — 로컬 검증 | 공유 병목에서 TCP 처리량과 지연이 어떻게 바뀌는가? | [20 Mbit/s 가상 링크 측정](../labs/08-ai-dc-network/evidence/2026-09-22.json); RoCE/ECN/PFC는 미검증 |
| 9 | [Edge Load Balancer HA](../labs/09-load-balancer-ha/README.md) — 로컬 검증 | 관리 서비스를 사용자 트래픽과 분리하면서 백엔드 장애에도 HTTP를 유지할 수 있는가? | [관리 SSH 허용·데이터 SSH 거부·정상/장애/복구 HTTP](../labs/09-load-balancer-ha/evidence/2026-10-01.json); NetScaler·F5·Cisco SD-WAN Manager·CVE·실제 HA는 미검증 |
| 10 | [Network Digital Twin](../labs/10-network-digital-twin/README.md) — 로컬 검증 | 읽기 전용 모델로 경로·정책·외부 의존성과 AIDC 통합 Control Plane의 환경별 관측 상태를 판정할 수 있는가? | [Fabric·Sovereign 경로와 Public·Private·On-Prem API 관측 판정](../labs/10-network-digital-twin/evidence/2026-10-02.json); 실제 장비·Cloud API·상용 Control Plane은 미검증 |
| 11 | [Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md) — 로컬 검증 | KEV와 공식 실제 악용 정보에 노출·중요도·관리 Plane·기한을 합치면 조치 순서가 어떻게 달라지는가? | [P0 4건·P1 1건·P2 1건·P3 2건과 출처 일치 검사](../labs/11-vulnerability-prioritization/evidence/2026-10-06.json); 실제 자산·패치는 미검증 |
| 12 | [AI Multi-Region Data Path](../labs/12-ai-multiregion-data-path/README.md) — 로컬 검증 | Hub 원본과 Spoke Cache로 반복 원본 요청을 줄이고 손상 파일만 복구할 수 있는가? | [Cold Miss 8·Warm Hit 8·손상 1건 감지·복구 후 전체 Hit](../labs/12-ai-multiregion-data-path/evidence/2026-10-06.json); AWS·Qumulo·HyperPod 대기 |
| 13 | [Kubernetes RBAC](../labs/13-kubernetes-rbac/README.md) — 로컬 검증 | Operator용 ServiceAccount를 Namespace 최소 권한으로 제한하고 허용·거부를 런타임에서 확인할 수 있는가? | [kind에서 허용 2개·거부 4개 모두 기대 일치](../labs/13-kubernetes-rbac/evidence/2026-09-30.json); Dell CSM·실제 Operator·Audit Log·운영 k3s는 미검증 |
| 14 | [Terraform Security Validation](../labs/14-terraform-security-validation/README.md) — 로컬 검증 | 문법상 유효한 공개 SSH 규칙을 배포 전에 찾고 수정본을 같은 정책으로 재검증할 수 있는가? | [Before CKV_AWS_24 실패 1건·After 통과 1건](../labs/14-terraform-security-validation/evidence/2026-10-06.json); AWS Apply·CI 차단·Continuum은 미검증 |

## 실습 README 공통 양식

1. 문제와 브리핑 출처
2. 범위·상태와 구성 환경
3. 토폴로지 및 설정
4. 정상 상태의 기대값과 실제 출력
5. 장애 또는 거부 경로 테스트
6. 복구와 재검증
7. 결과·한계·개인 프로젝트와의 연결

증적이 없으면 `Result`에 성공 문장을 먼저 채우지 않습니다. 장비 이미지·버전에 따라 명령이 다르면 사용 환경을 명시합니다.
