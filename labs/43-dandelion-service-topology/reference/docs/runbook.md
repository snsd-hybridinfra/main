<!-- STATUS: CURRENT -->

# Runbook

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 최신 운영 실행 절차를 정리한다.

멘토링 및 최종 발표 기준으로 다음 작업 흐름을 설명하기 위한 문서이다.

```text
Control Node
→ Ansible Playbook 실행
→ 서비스 구성
→ 모니터링 확인
→ 백업 실행
→ 복구 테스트
→ 운영 상태 검증
```

---

## 2. 실행 전제

| 항목 | 내용 |
|---|---|
| 실행 위치 | Control Node |
| 실행 도구 | Ansible, SSH, 운영 스크립트 |
| 대상 환경 | OpenStack 기반 인스턴스 |
| 관리 대상 | Web, DB, Proxy, Monitoring, Backup / Recovery Node |
| 최종 목표 | OpenStack Provisioning부터 운영 검증까지 자동화 |

현재는 생성된 인스턴스를 대상으로 구성 자동화와 운영 검증 자동화를 수행한다.  
OpenStack 인스턴스 생성 자동화는 `provision.yml` 보완 범위로 관리한다.

---

## 3. 전체 실행 흐름

최종 목표 기준 실행 흐름은 다음과 같다.

```text
1. OpenStack 리소스 생성
2. SSH 접속 가능 상태 확인
3. Inventory 구성 또는 갱신
4. 공통 환경 설정
5. Web 서비스 구성
6. DB 서비스 구성
7. Proxy / HAProxy 구성
8. Monitoring Stack 구성
9. Restic 백업 구성
10. 복구 테스트
11. 운영 검증
```

---

## 4. 권장 Playbook 실행 순서

```text
site.yml
├── provision.yml
├── wait-ssh.yml
├── common.yml
├── docker-swarm.yml
├── database.yml
├── proxy.yml
├── monitoring.yml
├── backup.yml
└── validate.yml
```

| 순서 | Playbook | 목적 | 현재 상태 |
|---:|---|---|---|
| 1 | provision.yml | OpenStack 인스턴스 / 보안그룹 / 볼륨 생성 | 보완 필요 |
| 2 | wait-ssh.yml | SSH 접속 가능 상태 확인 | 예정 |
| 3 | common.yml | 공통 패키지 / 시간대 / 기본 환경 설정 | 작성 / 검증 대상 |
| 4 | docker-swarm.yml | Docker Swarm 기반 Web 구성 | 구조 반영 |
| 5 | database.yml | MariaDB 및 Replica 구성 | 검증 진행 |
| 6 | proxy.yml | HAProxy 구성 | 구성 완료 / 검증 대상 |
| 7 | monitoring.yml | Prometheus / Exporter / Grafana / Alertmanager 구성 | 설치 완료 / 설정 진행 |
| 8 | backup.yml | Restic 및 백업 스크립트 구성 | Web / DB / Proxy 완료 |
| 9 | validate.yml | 서비스 / 모니터링 / 백업 / 복구 검증 | 작성 대상 |

---

## 5. 기본 실행 명령

Control Node에서 다음 순서로 실행한다.

```bash
cd ~/dandelion-cloud-automation/ansible

ansible-inventory -i inventory.ini --list

ansible all -i inventory.ini -m ping

ansible-playbook -i inventory.ini common.yml
ansible-playbook -i inventory.ini docker-swarm.yml
ansible-playbook -i inventory.ini database.yml
ansible-playbook -i inventory.ini proxy.yml
ansible-playbook -i inventory.ini monitoring.yml
ansible-playbook -i inventory.ini backup.yml
ansible-playbook -i inventory.ini validate.yml
```

`site.yml` 통합 실행 구조가 완성되면 다음 명령으로 통합 실행한다.

```bash
ansible-playbook -i inventory.ini site.yml
```

---

## 6. 실행 후 확인 항목

| 영역 | 확인 명령 / 방법 |
|---|---|
| Ansible 연결 | `ansible all -i inventory.ini -m ping` |
| 서버 시간 | `timedatectl` |
| Docker 상태 | `docker ps`, `docker service ls` |
| Web 응답 | `curl http://<proxy-or-service-ip>` |
| HAProxy 상태 | `systemctl status haproxy` |
| DB 상태 | `systemctl status mariadb` |
| DB 접속 | `mysql -u <user> -p -h <db-ip>` |
| Prometheus | Target Up 확인 |
| Grafana | Data Source / Dashboard 확인 |
| Alertmanager | 알림 Rule / Receiver 확인 |
| Restic | `restic snapshots` |
| 복구 테스트 | restore 결과 파일 / 서비스 상태 확인 |

---

## 7. 장애 발생 시 기본 대응 순서

```text
1. 인스턴스 상태 확인
2. 네트워크 / 보안그룹 확인
3. SSH 접속 확인
4. Ansible inventory 확인
5. 서비스 systemd 상태 확인
6. Docker / Swarm 상태 확인
7. 로그 확인
8. 백업 snapshot 확인
9. 복구 절차 실행
10. 결과 문서화
```

---

## 8. 멘토링 설명 기준

```text
현재 Runbook은 생성된 인스턴스 기반의 구성 자동화와 운영 검증 절차를 기준으로 작성했습니다.

최종 목표는 provision.yml을 추가하여 OpenStack 인스턴스 생성부터 site.yml 통합 실행까지 연결하는 것입니다.

따라서 본 Runbook은 현재 구현 범위와 최종 자동화 목표를 모두 반영한 운영 절차 문서입니다.
```
