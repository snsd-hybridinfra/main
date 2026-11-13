<!-- STATUS: COMPLETE -->

# Review Checklist

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 최종 제출 전 검수 기준을 정의한다.

본 프로젝트는 Phase 기반 구현 로드맵을 사용한다.

~~~text
Phase 1: 필수 구성 및 기본 검증 단계
Phase 2: 운영 확장 및 검증 고도화 단계
Phase 3: 도전 확장 단계
Out of Scope: 제외 범위
~~~

최종 검수의 목적은 Phase 1 필수 구성과 검증 산출물이 누락되지 않았는지 확인하고, 문서 전체의 용어, 구조, 범위, 산출물 기준이 일관되게 정리되었는지 확인하는 것이다.

---

## 2. 최종 검수 원칙

최종 제출 전에는 다음 기준을 우선 확인한다.

~~~text
1. Phase 1 필수 구성 완료 여부
2. 필수 캡처 확보 여부
3. Ansible / Docker / Proxy / Web / DB / Backup 흐름 검증 여부
4. Backup / Restore 절차 검증 여부
5. 문서 내 오래된 용어 제거 여부
6. Out of Scope 항목 명확화 여부
7. GitHub Repository와 Google Drive 제출자료 일치 여부
~~~

Phase 2와 Phase 3은 선택 또는 도전 확장 항목이므로, Phase 1 필수 검증이 완료된 이후에만 최종 산출물에 포함한다.

---

## 3. 용어 검수

| 체크 | 검수 항목 | 기준 |
|---|---|---|
| [ ] | Phase 1 용어 사용 | 필수 구성 및 기본 검증 단계 |
| [ ] | Phase 2 용어 사용 | 운영 확장 및 검증 고도화 단계 |
| [ ] | Phase 3 용어 사용 | 도전 확장 단계 |
| [ ] | Out of Scope 용어 사용 | 제외 범위 |
| [ ] | 오래된 등급 표현 제거 | A급 / B급 / B+ / C급 표현 제거 |
| [ ] | 서비스 명칭 통일 | WordPress / MariaDB / HAProxy |
| [ ] | 노드 명칭 통일 | Control / Proxy / Web / DB / Backup Node |
| [ ] | WordPress 역할 명확화 | 웹 개발 대상이 아니라 운영 서비스 대상 |
| [ ] | Cinder 역할 명확화 | DB 원본 저장소가 아니라 Backup Volume |
| [ ] | LB 역할 명확화 | Phase 1은 Reverse Proxy, Phase 3는 Load Balancing |

---

## 4. 금지 표현 검수

문서 전체에서 다음 표현이 남아 있지 않은지 확인한다.

~~~text
A급
B급
B+
C급
Nginx
nginx
web-test
docker run 기반 단순 배포
단일 서버 WordPress와 MariaDB 통합 구조
OpenStack LBaaS 필수 구현
Octavia 필수 구현
Kubernetes 필수 구현
Docker Swarm 필수 구현
~~~

검수 명령어:

~~~powershell
Select-String -Path README.md, docs\*.md, presentation\*.md -Pattern "A급|B급|B\+|C급|Nginx|nginx|web-test|docker run"
~~~

---

## 5. Phase 1 구성 검수

Phase 1은 최종 제출의 핵심 기준이다.

| 체크 | 검수 항목 | 완료 기준 |
|---|---|---|
| [ ] | OpenStack 인프라 구성 | 인스턴스 / 네트워크 / 라우터 / 서브넷 확인 |
| [ ] | Ubuntu 인스턴스 생성 | 필요한 노드 ACTIVE |
| [ ] | Control Node 구성 | Ansible 실행 가능 |
| [ ] | Proxy Node 구성 | HAProxy HTTP Reverse Proxy 실행 |
| [ ] | Web Node 구성 | Custom WordPress 컨테이너 실행 |
| [ ] | DB Node 구성 | MariaDB 서비스 실행 |
| [ ] | Backup / Validation Node 구성 | health_check / backup / restore 검증 가능 |
| [ ] | SSH 접속 확인 | Control Node에서 각 노드 접속 |
| [ ] | Ansible ping 확인 | 모든 Managed Node SUCCESS |
| [ ] | Playbook 실행 확인 | site.yml 실행 성공 |
| [ ] | Proxy 접속 확인 | Proxy Node 경유 WordPress HTTP 응답 |
| [ ] | DB 연결 확인 | Web Node에서 DB Node 3306 연결 |
| [ ] | Health Check 확인 | health_check.sh 실행 결과 확보 |
| [ ] | Backup 확인 | backup.sh 실행 결과 확보 |
| [ ] | Restore 확인 | restore.md 기반 복구 절차 검증 |
| [ ] | 장애 상황 정리 | 최소 1개 이상 장애 및 복구 기록 |

---

## 6. Phase 1 캡처 검수

| 체크 | 캡처 영역 | 필수 캡처 |
|---|---|---|
| [ ] | OpenStack | 인스턴스 목록 |
| [ ] | OpenStack | 네트워크 / 라우터 / 서브넷 |
| [ ] | OpenStack | 보안그룹 |
| [ ] | 접속 | Floating IP 또는 포트포워딩 구조 |
| [ ] | SSH | 각 노드 접속 성공 |
| [ ] | Ansible | ansible --version |
| [ ] | Ansible | ansible-inventory --list |
| [ ] | Ansible | ansible all -m ping |
| [ ] | Ansible | site.yml syntax check |
| [ ] | Ansible | site.yml 실행 결과 |
| [ ] | Docker | docker --version |
| [ ] | Docker | docker compose version |
| [ ] | Proxy | HAProxy 컨테이너 running |
| [ ] | Web | WordPress 컨테이너 running |
| [ ] | DB | MariaDB 서비스 running |
| [ ] | Port | ss -tulnp |
| [ ] | HTTP | Proxy Node 경유 WordPress 접속 |
| [ ] | DB | Web Node → DB Node 3306 연결 |
| [ ] | Validation | health_check.sh 실행 결과 |
| [ ] | Backup | backup.sh 실행 결과 |
| [ ] | Restore | restore.md 또는 복구 검증 결과 |
| [ ] | Troubleshooting | 장애 상황 및 복구 과정 |

---

## 7. 문서 검수

## 7.1 필수 문서 검수

| 체크 | 문서 | 검수 기준 |
|---|---|---|
| [ ] | README.md | 프로젝트 전체 흐름과 Phase 구조 반영 |
| [ ] | docs/architecture.md | Control / Proxy / Web / DB / Backup 구조 반영 |
| [ ] | docs/network-design.md | 보안그룹, 포트, 접속 경로 반영 |
| [ ] | docs/server-setup.md | WordPress / MariaDB / HAProxy 구성 반영 |
| [ ] | docs/ansible-automation.md | Ansible inventory, site.yml, roles 기준 반영 |
| [ ] | docs/validation-report.md | Phase 1 검증 기준 반영 |
| [ ] | docs/team-task-guide.md | 팀원별 역할 및 산출물 기준 반영 |
| [ ] | docs/pre-run-checklist.md | 실행 전 점검 기준 반영 |
| [ ] | docs/troubleshooting.md | 장애 대응 기준 반영 |
| [ ] | docs/runbook.md | 실제 실행 순서 반영 |
| [ ] | docs/scope-control.md | Phase 기반 범위 통제 반영 |
| [ ] | docs/implementation-roadmap.md | Phase별 구현 순서 반영 |
| [ ] | docs/final-deliverables.md | 제출 산출물 기준 반영 |
| [ ] | docs/review-checklist.md | 최종 검수 기준 반영 |
| [ ] | presentation/presentation-outline.md | 발표 흐름 반영 |

---

## 7.2 문서 품질 검수

| 체크 | 검수 항목 | 기준 |
|---|---|---|
| [ ] | 제목 구조 | Markdown heading 계층 일관 |
| [ ] | 표 형식 | 깨진 표 없음 |
| [ ] | 코드블록 | Markdown 코드블록 정상 |
| [ ] | 링크 | 내부 문서 링크 정상 |
| [ ] | 용어 | Phase 용어 통일 |
| [ ] | 범위 | Out of Scope 명확 |
| [ ] | 검증 | 명령어와 성공 기준 포함 |
| [ ] | 산출물 | 캡처 경로와 제출 기준 포함 |
| [ ] | 발표 가능성 | 발표자가 읽고 설명 가능한 수준 |

---

## 8. Ansible 검수

| 체크 | 항목 | 명령어 | 기준 |
|---|---|---|---|
| [ ] | Ansible 설치 | ansible --version | 버전 출력 |
| [ ] | Inventory 확인 | ansible-inventory --list | proxy / web / db / backup 그룹 표시 |
| [ ] | Ping 확인 | ansible all -m ping | 모든 노드 SUCCESS |
| [ ] | Syntax Check | ansible-playbook site.yml --syntax-check | 통과 |
| [ ] | Playbook 실행 | ansible-playbook site.yml | 실패 없음 |
| [ ] | Proxy 배포 | ansible proxy -a "docker ps" | HAProxy running |
| [ ] | Web 배포 | ansible web -a "docker ps" | WordPress running |
| [ ] | DB 배포 | ansible db -a "systemctl status mariadb running |

---

## 9. Docker / Service 검수

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | Docker 설치 | Proxy / Web / DB Node에서 Docker 확인 |
| [ ] | Compose 설치 | docker compose version 확인 |
| [ ] | MariaDB | mariadb service active |
| [ ] | WordPress | dandelion-wordpress running |
| [ ] | HAProxy | dandelion-haproxy running |
| [ ] | DB Port | DB Node 3306 listening |
| [ ] | Web Port | Web Node 80 listening |
| [ ] | Proxy Port | Proxy Node 80 listening |
| [ ] | DB Connection | Web Node에서 DB Node 3306 연결 |
| [ ] | HTTP Access | Proxy Node 경유 WordPress 접속 |

---

## 10. Backup / Restore 검수

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | health_check.sh | 실행 결과 확보 |
| [ ] | backup.sh | 실행 결과 확보 |
| [ ] | MariaDB dump | wordpress_db.sql 생성 |
| [ ] | WordPress files archive | wordpress_files.tar.gz 생성 |
| [ ] | Backup file size | 0 byte 아님 |
| [ ] | Backup path | backup/ 또는 /backup 경로 정리 |
| [ ] | restore.md | DB / files 복구 절차 포함 |
| [ ] | Restore warning | 기존 데이터 덮어쓰기 위험 명시 |
| [ ] | Restore validation | 복구 검증 결과 기록 |

---

## 11. Phase 2 검수

Phase 2는 선택 산출물이다.

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | HTTPS | curl -k 또는 브라우저 접속 확인 |
| [ ] | Redirect | HTTP 80 → HTTPS 443 확인 |
| [ ] | Cinder Volume | Volume 생성 및 attach 확인 |
| [ ] | /backup mount | df -h에서 확인 |
| [ ] | Cinder Backup | /backup 경로에 백업 결과 저장 |
| [ ] | node_exporter | metrics 출력 |
| [ ] | cAdvisor | metrics 출력 |
| [ ] | Prometheus | Target UP |
| [ ] | Grafana | Dashboard 화면 |
| [ ] | backup playbook | ansible-playbook backup.yml 실행 |
| [ ] | validate playbook | ansible-playbook validate.yml 실행 |
| [ ] | roles 구조 | ansible/roles 구성 확인 |

Phase 2가 일부 실패해도 Phase 1 산출물이 완성되어 있으면 제출 가능하다.

---

## 12. Phase 3 검수

Phase 3은 도전 확장 산출물이다.

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | Web Node 2 | 인스턴스 ACTIVE |
| [ ] | Web Node 2 Ansible ping | SUCCESS |
| [ ] | Web Node 2 WordPress | 컨테이너 running |
| [ ] | HAProxy backend | web1 / web2 등록 |
| [ ] | Round Robin | Web-1 / Web-2 응답 분산 |
| [ ] | Common DB | 두 Web Node가 동일 DB Node 연결 |
| [ ] | Failure Test | Web-1 중지 시 Web-2 응답 |

Phase 3에서는 다음 항목을 검수 대상에 포함하지 않는다.

~~~text
WordPress files 자동 동기화
wp-content/uploads 공유
plugin/theme 동기화
NFS 기반 WordPress shared storage
Object Storage 연동
DB Replication
DB Clustering
OpenStack LBaaS / Octavia
Auto Scaling
~~~

---

## 13. Repository 구조 검수

| 체크 | 경로 | 기준 |
|---|---|---|
| [ ] | README.md | 존재 |
| [ ] | docs/ | 주요 문서 존재 |
| [ ] | ansible/ | ansible.cfg, inventory.ini, site.yml 존재 |
| [ ] | docker/wordpress/ | Dockerfile, custom.ini 존재 |
| [ ] | docker/compose/ | Web / MariaDB service configuration 파일 존재 |
| [ ] | docker/proxy/ | HAProxy compose 및 haproxy.cfg 존재 |
| [ ] | scripts/ | health_check.sh, backup.sh 존재 |
| [ ] | screenshots/ | 검증 캡처 정리 |
| [ ] | presentation/ | 발표 개요 존재 |
| [ ] | submission/ | 제출 패키지 정리 |
| [ ] | tools/ | 상태 생성 / 검증 스크립트 존재 |
| [ ] | .github/workflows/ | GitHub Actions workflow 존재 |

---

## 14. Google Drive 제출 검수

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | 결과보고서 PPT | 업로드 완료 |
| [ ] | 결과보고서 PDF | 업로드 완료 |
| [ ] | 시연 영상 | 업로드 완료 |
| [ ] | 소스 코드 | GitHub URL 또는 zip 업로드 |
| [ ] | 회의록 | 날짜별 정리 |
| [ ] | 작업일지 | 팀원별 정리 |
| [ ] | 캡처 자료 | 영역별 정리 |
| [ ] | 트러블슈팅 자료 | 장애 / 조치 / 결과 포함 |
| [ ] | 기타 자료 | 멘토링 질문, 제출 체크리스트 포함 |

---

## 15. 발표자료 검수

| 체크 | 항목 | 기준 |
|---|---|
| [ ] | 프로젝트 배경 | 문제 정의 포함 |
| [ ] | 목표 | 자동화 / 운영 최적화 목표 명확 |
| [ ] | Phase 구조 | Phase 1 / 2 / 3 설명 |
| [ ] | 아키텍처 | Control / Proxy / Web / DB / Backup 구조 |
| [ ] | OpenStack | 인프라 구성 설명 |
| [ ] | Ansible | 자동화 흐름 설명 |
| [ ] | Docker | WordPress / MariaDB / HAProxy 설명 |
| [ ] | 검증 | 접속 / DB / 백업 / 복구 결과 |
| [ ] | 장애 대응 | 최소 1개 시나리오 포함 |
| [ ] | 한계 | Out of Scope 설명 |
| [ ] | 결과 | 최종 성공 기준 설명 |

---

## 16. 최종 제출 가능 조건

다음 조건을 만족하면 제출 가능 상태로 판단한다.

| 체크 | 조건 |
|---|---|
| [ ] | Phase 1 필수 구성 완료 |
| [ ] | Phase 1 필수 캡처 확보 |
| [ ] | 필수 문서 작성 완료 |
| [ ] | Ansible 실행 결과 확보 |
| [ ] | WordPress / HAProxy 컨테이너 및 MariaDB 서비스 실행 결과 확보 |
| [ ] | Proxy Node 경유 WordPress 접속 확인 |
| [ ] | Web Node → DB Node 연결 확인 |
| [ ] | Health Check 결과 확보 |
| [ ] | Backup 결과 확보 |
| [ ] | Restore 절차 검증 |
| [ ] | 장애 상황 1개 이상 정리 |
| [ ] | 결과보고서 / 발표자료 작성 |
| [ ] | 시연 영상 준비 |
| [ ] | Google Drive 제출자료 정리 |
| [ ] | GitHub Repository 최신 상태 |

---

## 17. 최종 검수 명령어

문서 내 오래된 표현 검수:

~~~powershell
Select-String -Path README.md, docs\*.md, presentation\*.md -Pattern "A급|B급|B\+|C급|Nginx|nginx|web-test|docker run"
~~~

Repository 상태 생성:

~~~powershell
python tools\generate_project_status.py
python tools\validate_repository.py
~~~

Git 상태 확인:

~~~powershell
git status
~~~

---

## 18. 핵심 검수 메시지

~~~text
최종 검수의 핵심은 기능 개수보다 Phase 1 필수 운영 흐름의 완성도이다.

OpenStack 인프라 구성, Ansible 자동화, Proxy/Web/DB/Backup Node 분리,
WordPress와 MariaDB/HAProxy 실행, Proxy 경유 접속,
Health Check, Backup, Restore, Troubleshooting 증거가 모두 확보되어야 한다.

Phase 2와 Phase 3은 추가 완성도를 보여주는 선택 산출물로 검수한다.
~~~



