# 출처와 자료 확보 범위

**확인 기준: 2026년 11월 2일 (월), 한국시간**

`브리핑 날짜`는 대화에서 다룬 날, `발행·갱신일`은 출처의 날짜, `확인일`은 이번 정리에서 문서를 확인한 날이다. 원문의 시각대가 분명하면 함께 표시한다. 발행일을 사건 발생일로 바꾸지 않는다.

## 이번에 공식 자료로 확인한 출처

아래 S01~S10의 확인일은 모두 **2026-11-02**다. 링크와 관련 본문을 확인했다는 뜻이며 제품·취약점·성능을 직접 검증했다는 뜻은 아니다. 버전별 수정 사항과 동적 문서는 실제 작업 시 다시 확인한다.

| ID | 원문 | 발행·갱신 또는 자료 기준 | 이번에 확인한 범위 |
|---|---|---|---|
| S01 | [Cisco Talos KeyDrift 분석](https://blog.talosintelligence.com/uat-11473-keydrift/) | 2026-10-28, 원문 표기 | CVE-2026-20127 악용, SD-WAN 제어면·키 자료 수집 분석 |
| S02 | [Palo Alto Networks PHP 취약점 공지](https://security.paloaltonetworks.com/CVE-2026-109618) | 2026-10-21 게시·10-29 갱신 표기 | CVE 두 건, 제품별 영향, 노출 관리 인터페이스 대상 악용과 접근 제한 권고 |
| S03 | [Cisco ASA/FTD SSL VPN 권고](https://www.cisco.com/c/en/us/support/docs/csa/cisco-sa-asaftd-tunnel-dos-s6mgkb75.html) | 2026-10-28 19:15 GMT | CVE-2026-76418, DoS 영향·기능/설정 조건·수정 소프트웨어 안내 |
| S04 | [Cisco Live BRKDCN-2634 PDF](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2026/pdf/BRKDCN-2634.pdf) | 2026년판, PDF 표기 | ACI BGW 기반 이기종 Fabric 연결의 목차·설계 설명 |
| S05 | [Cisco Live BRKOPS-1603 PDF](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2026/pdf/BRKOPS-1603.pdf) | 2026년판, PDF 표기 | NaC 데이터 모델, 사전 검증·배포·사후 시험 |
| S06 | [Neutron 2026.2 릴리스 노트](https://docs.openstack.org/releasenotes/neutron/2026.2.html) | 2026.2 시리즈, 동적 문서 | Route Leaking·PVLAN·특정 HA 보조 프로세스 변경 |
| S07 | [Neutron PVLAN 운영 문서](https://docs.openstack.org/neutron/2026.2/admin/config-pvlan.html) | 2026.2 버전 문서 | 포트 유형·Port Security 요구·기본 동작 |
| S08 | [neutron-lib 2026.2 릴리스 노트](https://docs.openstack.org/releasenotes/neutron-lib/2026.2.html) | 3.25.0 항목 | Gateway HA Chassis 우선순위 API·PVLAN 확장 |
| S09 | [데이터센터코리아 전체 프로그램](https://datacenterkorea.kr/conference-overview/) | 기준일 현재 사전 프로그램 | 행사 일정과 사후 자료를 찾을 세션 선별 |
| S10 | [데이터센터코리아 DC Tech Session](https://datacenterkorea.kr/program/dc-tech-session/) | 기준일 현재 사전 프로그램 | 11-05~06 기술 세션 안내. 발표 결과는 미확보 |

## 기존 기록을 종합한 출처

아래 문서는 이번 변경의 기준 커밋 `9dc77515d7fe258c767c1bcad6f60c3a7e304bd0`에서 읽었다. 기존 문서가 연결한 과거 기사와 증적을 이번 정리에서 모두 재실행·재검증하지 않았다.

| 기존 문서 | 누적 정리에서의 역할 |
|---|---|
| [뉴스 → 기술 실습](../news-to-labs.md) | 9월~10월 중순 기사·질문·랩·증적·한계 연결 |
| [기술 흐름](../industry-trends.md) | AIDC·Fabric·Cloud·보안·관측·복구 등 기존 분류 |
| [실습 로드맵](../lab-roadmap.md) | 14개 랩의 기존 상태와 증적 위치 |
| [업데이트 기록](../update-log.md) | 09-22~10-18의 변경·실행 기록 |
| [커리어 로드맵](../career-roadmap.md) | 네트워크에서 자동화·클라우드·보안·AI 인프라로 확장하는 학습 순서 |

정리 전 기존 기록은 [기준 커밋의 docs](https://github.com/snsd-hybridinfra/main/tree/9dc77515d7fe258c767c1bcad6f60c3a7e304bd0/docs)에서 구분해 볼 수 있다.

## 원문 확보가 불완전한 부분

| 구간·항목 | 상태 | 처리 |
|---|---|---|
| 09-08~09-21 일별 기사 전체 | 전체 원문 미확보 | 기존 초기 주제와 편집 기준만 종합 |
| 09-22~10-18 일별 기사 전체 | 저장소의 선별 정리 확보 | 일별 10개 기사 전체 아카이브로 표현하지 않음 |
| 10-19~10-27 | 이번 검색에서 일별 본문 미확보 | 해당 기간의 뉴스 제목·출처를 추정해 생성하지 않음 |
| 10-28~10-31 | 일부 항목 확보 | 공식 확인한 세 보안 이슈와 컨퍼런스 기술을 반영 |
| 11-01~11-02 | 이번 검색에서 일별 본문 미확보 | 해당 날짜의 완성된 브리핑 파일을 생성하지 않음 |
| 10-28 KT 400G 연결망·SK하이닉스 실적 언급 | 검색된 과거 요약은 있으나 이번 정리에 필요한 원문 확인 미완료 | 새로운 확인 사실로 수록하지 않음 |
| 10-30 AI 인프라 프런티어 행사 언급 | 공식 근거 확인 미완료 | 행사 실적·개최 사실을 확정해 쓰지 않음 |
| 10-31 GitLab 항목 | 검색 결과에서 제목·식별자가 불완전 | CVE·영향을 추정하지 않음 |
| 데이터센터코리아 발표자료·녹화 | 기준일 현재 미확보 | 사전 프로그램과 향후 확인 질문만 기록 |

과거 검색 요약은 누락 구간을 찾는 단서로 사용했다. 요약에서 원문이 축약됐거나 불완전한 항목은 위 공식 출처로 보완한 경우에만 새로운 사실로 확정했다. 투자액·MW·CVE 총건수·채용 수요처럼 재확인하지 못한 수치는 새 누적 요약에 옮기지 않았다.
