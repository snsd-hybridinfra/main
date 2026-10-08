# 업데이트 기록

## 2026-09-22 — 초기 정리

- 처음 공유한 GitHub 정리안의 8개 실습 주제를 로드맵으로 구성.
- 「IT·보안 데일리 브리핑」의 누적 요약을 기술 흐름과 커리어 로드맵으로 분류.
- `F:\main`을 주 저장소, `snsd-multicloud-ops`를 연결된 서브 프로젝트로 구분.

## 2026-09-22 — BGP/ECMP 첫 실습

- WSL2 FRR 10.7.0에서 2 Spine·2 Leaf·2 Host 토폴로지를 구성.
- 정상 경로 2개, Spine1 중단 후 Spine2 경로 1개와 Host 간 ping 3/3, 복구 후 경로 2개와 ping 3/3 확인.
- [설정과 정제 출력](../labs/01-bgp-ecmp/README.md)을 추가하고 상태를 로컬 검증으로 변경.

## 2026-09-22 — EVPN/VXLAN 두 번째 실습

- FRR 두 Leaf와 VNI 100·200의 BGP EVPN 제어면 및 VXLAN dataplane 구성.
- 같은 VNI의 Host 간 ping은 각각 3/3, 다른 VNI의 Host 간 ping은 0/2 확인.
- [설정과 출력](../labs/02-evpn-vxlan/README.md)을 추가하고 상태를 로컬 검증으로 변경.

## 2026-09-22 — RESTCONF/Python 접근 확인

- Cisco DevNet 공개 IOS XE 장비 두 곳에서 RESTCONF 인터페이스 GET을 시도했으나 공개 예시 계정이 HTTP 401을 반환.
- [읽기 전용 대조 코드](../labs/03-restconf-python/README.md)와 거부 증적을 추가. API·CLI 일치는 검증하지 않았으므로 상태는 설계.
## 2026-09-22 — IAM/STS 설계와 백업·복구 실습

- [IAM/STS 예시 정책](../labs/04-iam-sts/README.md) 4개의 JSON 구문 확인. AWS 계정에서 위임·허용·거부·만료를 실행하지 않아 설계로 표시.
- [백업·복구](../labs/05-backup-recovery/README.md): 합성 HTTP/SQLite 서비스에서 5건 중 3건 복원, 2건 손실, RTO 1.627초 측정. 없는 백업 복원은 실패했고 유효한 스냅샷으로 재시도했다.
## 2026-09-22 — AAA/RADIUS 인증 판정

- [FreeRADIUS 로컬 실습](../labs/06-aaa-radius/README.md)에서 등록 계정 인증 1건, 틀린 비밀번호와 미등록 계정 거부 2건을 확인.
- 실제 네트워크 장비의 관리망 접근은 포함하지 않았다.
## 2026-09-22 — Agent 경계와 가상 링크 혼잡 실습

- [AI Agent Security](../labs/07-ai-agent-security/README.md): 결정적 로컬 게이트에서 도구·경로·외부 통신·호출 비용·합성 승인 경계를 확인. 실제 LLM Agent·사람 승인은 미검증.
- [AI DC Network](../labs/08-ai-dc-network/README.md): 격리된 가상 링크 20 Mbit/s 병목에서 단일 TCP 19.07 Mbit/s, 2개 흐름 합계 19.06 Mbit/s, 부하 중 ping 평균 69.16 ms를 측정. RoCE/ECN/PFC는 미검증.
## 2026-09-22 — 뉴스에서 기술을 검증하는 구조로 정리

- ChatGPT 웹의 「IT·보안 데일리 브리핑」과 기사 원문을 대조해 [뉴스 → 기술 실습 기록](news-to-labs.md)을 만들었다.
- 8개 실습에 **원문 → 내 질문 → 실제 증적 → 미검증 범위**를 연결했다. 기사에 없는 구현은 내 실험 설계로 표시했다.
- 기존 검증 상태는 유지했다: 6개 로컬 검증, RESTCONF/Python·IAM/STS 2개 설계.

## 2026-09-24 — F5 권고에서 Load Balancer HA 실습으로

- 9월 23일 브리핑의 F5 BIG-IP APM 이슈를 F5 권고와 CISA KEV 공지로 확인했다.
- 보안 권고에서 가용성 질문을 도출해 [Nginx Load Balancer HA 실습](../labs/09-load-balancer-ha/README.md)을 추가했다.
- 정상 4:4 분산, `web01` 중단 중 `web02` 응답 8/8, 복구 후 4:4 재분산을 확인했다. F5 제품·OAuth·취약점은 재현하지 않았다.

## 2026-09-26 — 애플리케이션 경로를 Network Digital Twin으로 검증

- 9월 24일 브리핑의 Network Digital Twin 흐름을 IP Fabric의 2026-09-23 애플리케이션 인프라 매핑 글과 8.1 릴리스 노트로 확인했다.
- [Network Digital Twin 실습](../labs/10-network-digital-twin/README.md)을 추가해 합성 애플리케이션 경로와 세그멘테이션 의도를 읽기 전용으로 계산했다.
- 정상 상태 2개 경로, spine1 중단 후 1개 경로, 두 Spine 중단 후 0개 경로, `guest → admin` 정책 거부를 확인했다.
- IP Fabric 제품, 실제 장비/API, 자동 수집, 라우팅 수렴, ACL/NAT·포트 판정은 검증하지 않았다.

## 2026-09-27 — CISA KEV에서 취약점 우선순위 실습으로

- 9월 26일 브리핑의 RouterOS·SharePoint 실제 악용 항목을 CISA KEV 공식 JSON에서 확인했다.
- [Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md)에 공식 CVE·기한과 합성 자산 맥락을 분리해 기록했다.
- KEV·인터넷 노출·중요도·관리 Plane·기한을 결합한 로컬 규칙으로 P0 2건, P2 1건, P3 2건을 계산했다.
- 실제 자산 버전·노출·패치 상태와 패치 후 검증은 수행하지 않았다.

## 2026-09-28 — 저장소 역할과 상태 중심으로 재구성

- README를 완료 목록 중심에서 **현재 상태 → 분야별 실습 → 문서 역할 → 저장소 경계** 순서로 재구성했다.
- 11개 실습을 Network & Data Center, Cloud & Automation, Security & Operations로 묶고 9개 로컬 검증·2개 설계 상태를 표시했다.
- [프로젝트 연결 지도](project-map.md)를 서브 프로젝트의 최신 권위 문서와 대조해 Stage별 실제 상태와 실습별 승격 조건을 정리했다.
- `snsd-multicloud-ops` 구현 파일과 상태는 변경하지 않았다.

## 2026-09-28 — Workload Identity 최소 권한 로컬 검증

- 9월 28일 브리핑의 Workload Identity 파괴 공격을 Microsoft Storm-3168 공식 분석으로 확인했다.
- 기존 IAM/STS 설계에 제한된 로컬 정책 평가기와 정상·거부 시나리오 7개를 추가했다.
- 지정 호출자와 버킷 목록 조회 2건은 허용됐고, 비신뢰 호출자·세션 범위 밖 조회·쓰기·삭제 5건은 거부됐다.
- AWS/Azure 런타임, STS 발급·만료, 자격증명 회전, Azure Resource Lock은 검증하지 않았다.
- 전체 상태를 로컬 검증 10개·설계 1개로 갱신했다.

## 2026-09-29 — Edge 관리망 분리 검증과 AI 데이터 경로 설계

- Citrix의 2026-09-27 NetScaler 보안 공지와 관리·데이터 Plane 분리 문서를 원문으로 확인했다.
- 중복 랩을 만들지 않고 기존 [09 Edge Load Balancer HA](../labs/09-load-balancer-ha/README.md)에 관리·데이터 Plane 분리를 통합했다. Admin→관리 주소 SSH 성공, 데이터망→SSH 거부, 정상·복구 시 두 백엔드 응답, Web01 중단 중 Web02 8/8를 확인했다.
- NetScaler 제품·공지 CVE·실제 NSIP/SNIP/VIP·ACL·HA는 실행하지 않았다.
- AWS의 2026-09-25 HyperPod·Qumulo 글을 바탕으로 [AI Multi-Region Data Path](../labs/12-ai-multiregion-data-path/README.md)를 설계 상태로 추가했다. 기사 수치는 내 측정값으로 기록하지 않았다.
- 기존 IAM/STS 랩의 다음 단계에 실제 AssumeRole, 허용·거부 API, CloudTrail 감사 확인을 명시했다.
- 전체 상태는 기존 랩 통합 후 로컬 검증 10개·설계 2개다.

## 2026-09-29 — 설계 상태 실습을 로컬 실행으로 전환

- [03 RESTCONF/Python](../labs/03-restconf-python/README.md)에 합성 HTTPS RESTCONF와 SSH CLI 장비를 추가했다. 인터페이스 3개 상태가 모두 일치했고 잘못된 비밀번호는 HTTP 401과 종료 코드 2로 거부됐다.
- 기존 공개 샌드박스 HTTP 401 증적은 남겼다. 이번 통과는 실제 IOS XE 장비 결과가 아니라 합성 장비에서 비교 로직을 끝까지 실행한 결과다.
- [12 AI Multi-Region Data Path](../labs/12-ai-multiregion-data-path/README.md)에서 4 MiB 합성 Dataset을 사용해 Cold Miss 8건, Warm Hit 8건, Warm Hub 요청 0건과 Cache 훼손 감지를 확인했다.
- 60 ms는 실제 WAN 측정값이 아니라 Cold Fetch마다 넣은 지연 모델이다. AWS·Qumulo·HyperPod와 NFS는 실행하지 않았다.
- 전체 상태를 로컬 검증 12개·설계 0개로 갱신했다.

## 2026-09-29 — FRR 구성 경고 제거 후 재실행

- 01 BGP/ECMP와 02 EVPN/VXLAN의 첫 증적에는 결과가 통과했어도 vtysh.conf 누락에 따른 FRR 구성 처리 경고가 함께 찍혀 있었다.
- 두 FRR 이미지에 빈 vtysh.conf와 올바른 소유권을 추가하고 WSL2에서 다시 실행했다.
- BGP/ECMP는 정상 2경로, Spine1 중단 후 1경로와 ping 3/3, 복구 후 2경로와 ping 3/3을 경고 없이 확인했다.
- EVPN/VXLAN은 VNI 100·200 각각 ping 3/3과 VNI 간 ping 0/2를 경고 없이 확인했다.
- 기존 2026-09-22 출력은 지우지 않고 새 [BGP/ECMP 증적](../labs/01-bgp-ecmp/evidence/2026-09-29.txt)과 [EVPN/VXLAN 증적](../labs/02-evpn-vxlan/evidence/2026-09-29.txt)을 추가했다.

## 2026-09-30 — 겹치는 랩은 확장하고 Kubernetes RBAC는 실행

- 삼성·SKT·하나금융의 2026-09-28 Private 5G 발표를 확인했다. Network Slicing은 기존 02 EVPN/VXLAN의 논리 세그먼트 질문과 겹쳐 새 랩을 만들지 않고 연결했다. 5G SA Core·USIM·금융망은 검증하지 않았다.
- AWS의 2026-09-28 Sovereign Cloud 독립 운영 시험 발표를 기존 10 Network Digital Twin에 통합했다. Global Backbone과 운영 전송 노드를 제거한 뒤에도 합성 EU Internet·Direct Connect 경로가 각각 1개 남는 것을 계산했다. AWS가 예고한 2026-10-24 실제 시험 결과를 성공으로 기록하지 않았다.
- Unit 42의 2026-09-29 Kubernetes Operator 연구는 기존 랩에 없는 Kubernetes 런타임 권한 질문이라 13 Kubernetes RBAC로 추가했다. kind v1.36.4에서 같은 Namespace의 Pod·Deployment 조회 2개는 허용되고 Secret 조회·Pod 삭제·다른 Namespace·ClusterRole 조회 4개는 거부됐다.
- 첫 실행에서 PowerShell 인수 전달과 `kubectl auth can-i`의 예상 거부 종료 코드·경고 출력을 발견해 스크립트를 고쳤다. 최종 재실행은 6/6 통과했고 임시 클러스터와 kubeconfig를 정리했다.
- NetScaler 공격 확대 후속 원문은 기존 09 Edge Load Balancer HA 항목에 합쳤다. 같은 주제의 새 랩은 추가하지 않았다.
- 전체 상태는 로컬 검증 13개·설계 0개다.

## 2026-10-01 — 실제 악용 정보를 기존 랩에 통합

- Cisco의 2026-09-30 Catalyst SD-WAN Manager 권고와 Microsoft의 2026-09-30 Zimbra 공격 분석을 원문으로 확인했다.
- 같은 주제의 랩을 늘리지 않고 [11 Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md)을 확장했다. CISA KEV 2건과 공식 실제 악용 2건을 합성 자산 맥락에 연결해 P0 3건, P1 1건, P2 1건, P3 2건을 계산했고 순서·등급·출처 일치 검사를 모두 통과했다.
- Cisco의 관리 Plane 노출 문제는 기존 [09 Edge Load Balancer HA](../labs/09-load-balancer-ha/README.md)의 관리·데이터망 분리 질문에 연결했다. 첫 재실행은 Docker Desktop 서비스가 중지돼 Compose 전 단계에서 멈췄다. Docker Desktop을 다시 시작한 뒤 재실행해 Admin SSH 허용, 데이터망 SSH 거부, 정상·복구 시 양쪽 백엔드 응답, Web01 중단 중 Web02 8/8을 확인했고 [2026-10-01 증적](../labs/09-load-balancer-ha/evidence/2026-10-01.json)을 저장했다.
- OpenStack 2026.2 Hibiscus의 2026-09-30 공식 릴리스는 산업 흐름에만 반영했다. Hibiscus 설치·업그레이드나 실제 Private Cloud 런타임은 검증하지 않았다.
- 랩 수는 로컬 검증 13개·설계 0개로 유지했다.
## 2026-10-02 — AIDC 운영 플랫폼을 기존 Digital Twin에 통합

- 10월 2일 브리핑에서 KT클라우드의 AIDC 운영 플랫폼과 네이버클라우드의 AI Factory 풀스택 보도를 확인했다. 두 원문은 2026-10-01에 발행됐다.
- GPU 규모보다 Cloud 운영 소프트웨어, Network·Storage·Security와 Public·Private·On-Prem 통합 Control Plane이 중요하다는 문제를 기존 [10 Network Digital Twin](../labs/10-network-digital-twin/README.md)의 의존성·관측 질문에 연결했다.
- 합성 Control Plane에서 Public·Private·On-Prem API 경로가 각각 1개 존재함을 확인했다. Private Cloud API를 비활성화한 시나리오에서는 Public·On-Prem 경로는 유지되고 Private 경로만 0개로 판정됐다. 전체 기존·추가 시나리오가 통과했다.
- 이는 기사 기업의 제품을 실행한 결과가 아니다. GPU Scheduling, 실제 Cloud API, Monitoring, 장애 복구와 서비스 성능은 검증하지 않았다.
- 새 랩을 만들지 않아 전체 상태는 로컬 검증 13개·설계 0개다.

## 2026-10-06 — 손상된 Spoke Cache 복구 재실행

- 새 랩을 만들지 않고 [12 AI Multi-Region Data Path](../labs/12-ai-multiregion-data-path/README.md)의 기존 무결성 실패 경로를 복구까지 확장했다.
- 4 MiB 합성 Dataset의 Cache 파일 1개를 고의로 훼손했다. SHA-256 불일치를 찾은 뒤 해당 파일만 Hub에서 다시 가져왔고, 같은 Epoch에서 8/8 해시 일치를 확인했다.
- 바로 다음 Epoch는 Cache Hit 8건, Hub 요청 0건, 무결성 실패 0건으로 돌아왔다. 이 복구 절차는 내 실험 설계이며 AWS·Qumulo 기능 검증이 아니다.
- 실제 AWS Region, Qumulo, NFS, HyperPod, WAN 성능과 비용은 계속 미검증 범위다. 전체 상태는 로컬 검증 13개·설계 0개로 유지했다.

## 2026-10-06 — 10월 3~6일 브리핑 검토와 IaC 보안 검증

- 10월 3~6일 브리핑을 다시 읽고 공식 원문을 확인했다. 반복된 Cloud Security·Agent Identity·AIDC 전력·광 네트워크 주제는 기존 흐름에 합쳤다.
- CISA KEV의 FortiMail CVE-2026-104286을 기존 [11 Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md)에 추가했다. 합성 FortiMail 자산은 115점 P0였고 전체 8개 자산의 순서·등급·출처 일치 검사가 통과했다.
- Dell DSA-2026-448은 기존 [13 Kubernetes RBAC](../labs/13-kubernetes-rbac/README.md)의 다음 검증 범위로만 연결했다. Dell CSM은 배포하거나 공격하지 않았다.
- 기존 랩에 없던 IaC 변경의 탐지·수정·재검증 질문은 [14 Terraform Security Validation](../labs/14-terraform-security-validation/README.md)으로 추가했다. Terraform Validate는 Before·After 모두 통과했고, Checkov `CKV_AWS_24`는 공개 SSH Before 1건 실패·수정 After 1건 통과였다.
- 첫 14번 실행은 Checkov `--quiet`의 통과 상세 생략을 검증식이 고려하지 못해 전체 판정만 실패했다. 파서를 고친 재실행은 네 조건 모두 통과했다.
- AWS 자격증명과 Apply를 사용하지 않았다. AWS Continuum·Google Agent, 실제 Security Group, CI Merge 차단은 미검증이다. 전체 상태는 로컬 검증 14개·설계 0개다.


## 2026-10-08 — 10월 7~8일 브리핑을 기존 랩에 통합

- 10월 7~8일 브리핑에서 KT클라우드 청라 AIDC, Microsoft MXC, Exchange Server 보안 업데이트를 원문으로 다시 확인했다.
- 청라 AIDC의 거점 간 연속성은 새 랩을 만들지 않고 [01 BGP/ECMP](../labs/01-bgp-ecmp/README.md)의 DCI 관점에 연결했다. 기존 FRR 증적을 KT클라우드 실제 망 검증으로 해석하지 않았다.
- [07 AI Agent Security](../labs/07-ai-agent-security/README.md)에 허용 Agent ID와 정확한 루프백·보고서 경로 검사를 추가했다. 허용 3개와 거부 8개가 기대와 일치했고, 외부 요청은 실행되지 않았다.
- [11 Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md)에 Exchange Server CVE-2026-96940을 추가했다. Microsoft 패치 권고만 확인돼 KEV·실제 악용 점수를 주지 않았고, 합성 Exchange 자산은 40점 P2였다. 전체 9개 자산의 순서·등급·출처 일치 검사가 통과했다.
- MXC·Exchange Server·KT클라우드 DCI는 배포하거나 공격하지 않았다. 랩 수는 로컬 검증 14개·설계 0개로 유지했다.

## 이후 갱신 양식

### YYYY-MM-DD

- **새 소식:** 출처, 보도일, 사건일.
- **기존 흐름과의 관계:** 강화 / 수정 / 새 주제.
- **학습·실습에 반영:** 바뀐 파일과 이유.
- **검증 상태:** 계획 / 설계 / 로컬 검증 / 런타임 검증.
