# 컨퍼런스·공식 기술자료 노트

**2026년 11월 2일 (월) 기준**  
10월 30일 컨퍼런스 브리핑의 세 가지 기술 주제를 공식 자료로 보완했다. 원문의 기술 설명과 아래의 개인 실습 계획을 구분한다.

## Cisco Live 2026 — 서로 다른 Fabric 연결

**세션:** BRKDCN-2634  
**자료:** [공식 발표 PDF](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2026/pdf/BRKDCN-2634.pdf) · [S04](source-register.md)

발표는 ACI Border Gateway를 이용한 이기종 VXLAN EVPN Fabric 연결을 다룬다. 제어면·데이터면, 도메인 사이 식별자 정규화, 분산 게이트웨이, 보안 정책이 주요 축이다. PDF 기준 3쪽은 목차, 5~8쪽은 Fabric 연결 방식 비교다.

**개인 학습 질문:** Fabric 내부와 경계의 역할을 나누고, VRF·VNI·경로 교환·게이트웨이·격리 정책이 맞물리는 위치를 설명한다.

**연결 랩:** [01 BGP/ECMP](../../labs/01-bgp-ecmp/README.md)·[02 EVPN/VXLAN](../../labs/02-evpn-vxlan/README.md)·[10 Digital Twin](../../labs/10-network-digital-twin/README.md).

**확장 계획:** 합성 두 Fabric의 경계와 허용 경로를 설계한다. 같은 테넌트 통신, 다른 테넌트 거부, 경계 장애 후 대체 경로를 시험 항목으로 둔다. FRR 기반 모델을 만들더라도 ACI 제품 구현을 검증했다는 의미로 사용하지 않는다.

## Cisco Live 2026 — Network as Code 검증

**세션:** BRKOPS-1603  
**자료:** [공식 발표 PDF](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2026/pdf/BRKOPS-1603.pdf) · [S05](source-register.md)

발표는 네트워크 상태를 데이터 모델로 관리하고, 변경 전 모델 검사와 배포 후 상태 시험을 연결한다. `nac-validate`의 구문·의미 검증과 `nac-test`의 시험 실행을 구분한다. PDF 기준 21쪽은 구성요소, 33~34쪽은 변경 흐름·사전 검사다.

**개인 학습 질문:** 설정 파일이 문법상 맞는 것과 실제 통신·격리가 의도대로 유지되는 것을 따로 확인한다.

**연결 랩:** [03 RESTCONF/Python](../../labs/03-restconf-python/README.md)·[10 Digital Twin](../../labs/10-network-digital-twin/README.md)·[14 Terraform Security Validation](../../labs/14-terraform-security-validation/README.md).

**확장 계획:** 합성 장비의 변경 전후 스냅샷과 기대값을 비교해 정상·오류·수집 실패를 나눈다. 처음에는 읽기 전용 검사를 만든다. 자동 배포·CI 차단·원복은 실행 증적이 생긴 뒤 별도 단계로 올린다.

## OpenStack 2026.2 — Fabric 연결과 격리

**자료:** [Neutron 릴리스 노트](https://docs.openstack.org/releasenotes/neutron/2026.2.html) · [PVLAN 운영 문서](https://docs.openstack.org/neutron/2026.2/admin/config-pvlan.html) · [neutron-lib 릴리스 노트](https://docs.openstack.org/releasenotes/neutron-lib/2026.2.html)  
**출처:** [S06·S07·S08](source-register.md)

| 확인한 기능 | 기술 요점 | 개인 실습 질문 |
|---|---|---|
| OVN BGP Route Leaking | 조건을 갖춘 Geneve 서브넷의 경로를 물리 Fabric에 광고. 기본적으로 관리자 작업 | 광고 허용 범위와 외부 도달성을 어떻게 제한·확인할까? |
| OVN Gateway HA API | Chassis 우선순위 조회·설정으로 장애 전환 순서를 표현 | 우선순위 설정과 실제 장애 후 활성 경로가 일치할까? |
| Private VLAN | Promiscuous·Isolated·Community로 같은 네트워크 안의 통신을 제한 | 허용·거부 통신표가 실제 패킷 결과와 맞을까? |

PVLAN은 네트워크와 포트의 Port Security가 필요하다. 유형을 생략한 포트는 Promiscuous가 기본값이므로, 기능을 켠 것만으로 격리가 완성됐다고 판단하면 안 된다.

10월 30일 브리핑의 메모리 감소 수치는 Neutron 전체나 모든 OVN HA의 성능 향상으로 해석하지 않는다. 공식 릴리스 노트는 특정 `neutron-keepalive-state-change` 구현 변경을 설명한다. 이 저장소에서 직접 측정한 수치가 아니다.

**연결 랩:** 01·02의 라우팅·격리 개념에서 출발한다. OpenStack/OVN 설치·업그레이드·게이트웨이 전환·PVLAN 동작은 이번에 실행하지 않았다. OpenInfra Live 영상의 회차·발표일도 이번 자료 확인만으로 확정하지 않는다.

## 데이터센터코리아 2026 — 사후에 볼 자료 선별

공식 안내의 행사 일정은 **2026-11-04~11-06**, 장소는 서울 aT센터다. 기준일 현재 행사 전이므로 아래는 프로그램을 보고 고른 **사후 확인 목록**이다. 발표자료·녹화·성과를 이미 확보했다는 의미가 아니다.

| 우선순위 | 공식 프로그램에서 선별한 주제 | 이후 확인할 질문 |
|---|---|---|
| 1 | 11-04 장애 분석 세션 | 장애 원인·영향 범위·복구 시간을 어떤 근거로 분류하는가? |
| 1 | 11-05 디지털트윈·통합 엔지니어링 세션 | IT 경로와 시설 의존성을 어떻게 연결하고 관측하는가? |
| 1 | 11-06 지능화·워크플로, 운영 솔루션 세션 | 이벤트·작업·승인·복구 검증이 어떻게 이어지는가? |
| 2 | 고밀도 인프라·전력·액체냉각 관련 세션 | 네트워크·서버 장애와 시설 제약을 어떻게 구분하는가? |

DC Tech Session도 냉각·전력·센싱 자료를 찾는 후속 경로로 둔다. 자료가 공개되면 발표자가 실제 제시한 아키텍처·시험 조건·제약을 확인하고 05·08·10번 랩과 연결한다. 현재는 학습 질문만 기록했다.

출처: [전체 프로그램](https://datacenterkorea.kr/conference-overview/)·[DC Tech Session](https://datacenterkorea.kr/program/dc-tech-session/) ([S09·S10](source-register.md)).
