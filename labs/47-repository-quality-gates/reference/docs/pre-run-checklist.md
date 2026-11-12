<!-- STATUS: CURRENT -->

# Pre-run Checklist

## 1. 문서 목적

본 문서는 Ansible Playbook 실행 전 점검해야 할 항목을 정리한다.

실행 전 점검 대상은 다음과 같다.

```text
Control Node
OpenStack 환경
SSH 연결
Inventory
Managed Nodes
Service Dependencies
Monitoring
Backup / Recovery
```

---

## 2. Control Node 점검

| 점검 항목 | 확인 방법 | 상태 |
|---|---|---|
| Ansible 설치 | `ansible --version` | 확인 필요 |
| SSH Key 존재 | `ls -al ~/.ssh` | 확인 필요 |
| Inventory 파일 존재 | `ls -al inventory.ini` | 확인 필요 |
| ansible.cfg 존재 | `ls -al ansible.cfg` | 확인 필요 |
| Playbook 존재 | `ls -al *.yml` | 확인 필요 |
| Python OpenStack SDK | `python3 -c "import openstack"` | Provisioning 자동화 시 필요 |

---

## 3. OpenStack 환경 점검

| 점검 항목 | 확인 내용 |
|---|---|
| 인증 정보 | clouds.yaml 또는 OpenStack RC 정보 확인 |
| Flavor | 노드별 리소스 생성 가능 여부 |
| Image | Ubuntu 이미지 사용 가능 여부 |
| Network | 관리 / 서비스 네트워크 확인 |
| Security Group | SSH, HTTP, HTTPS, Monitoring 포트 정책 |
| Floating IP | Control 또는 Proxy 접근용 IP |
| Cinder Volume | Backup / Recovery Node 연결 가능 여부 |

---

## 4. SSH 연결 점검

```bash
ansible all -i inventory.ini -m ping
```

성공 기준:

```text
모든 Managed Node에서 pong 응답 확인
```

실패 시 확인 항목:

```text
- IP 주소
- SSH 사용자
- SSH Key 권한
- Security Group SSH 허용
- known_hosts 충돌
- 인스턴스 상태
```

---

## 5. Inventory 점검

Inventory에는 최소 다음 그룹이 포함되어야 한다.

```ini
[control]
control-node

[proxy]
proxy-node

[web]
web-node

[db]
db-node

[monitoring]
monitoring-node

[backup]
backup-node
```

검증 명령:

```bash
ansible-inventory -i inventory.ini --list
```

---

## 6. 서비스 실행 전 점검

| 영역 | 점검 항목 |
|---|---|
| Common | apt lock, network, DNS, time sync |
| Web | Docker 설치 가능 여부, Docker Swarm 초기화 가능 여부 |
| Proxy | HAProxy 설치 가능 여부, 80 / 443 포트 충돌 여부 |
| DB | MariaDB 포트, 계정, Replica 구성 가능 여부 |
| Monitoring | Prometheus / Grafana 포트 사용 가능 여부 |
| Backup | Restic repository, Cinder mount, 권한 |

---

## 7. 포트 점검

| 서비스 | 기본 포트 |
|---|---:|
| SSH | 22 |
| HTTP | 80 |
| HTTPS | 443 |
| MariaDB | 3306 |
| Prometheus | 9090 |
| Grafana | 3000 |
| Alertmanager | 9093 |
| node_exporter | 9100 |
| cAdvisor | 8080 |
| mysqld_exporter | 9104 |
| blackbox_exporter | 9115 |

확인 명령:

```bash
ss -lntp
```

---

## 8. 백업 실행 전 점검

| 점검 항목 | 확인 방법 |
|---|---|
| Restic 설치 | `restic version` |
| Repository 접근 | `restic snapshots` |
| 백업 저장소 마운트 | `df -h` |
| DB Dump 가능 여부 | `mysqldump --version` |
| Web 파일 경로 | WordPress / Docker volume 경로 확인 |
| Proxy 설정 경로 | HAProxy 설정 파일 경로 확인 |
| Monitoring 백업 | Monitoring 구성 완료 후 추가 |

---

## 9. 실행 가능 기준

Playbook 실행 전 다음 조건을 만족해야 한다.

```text
1. Control Node에서 모든 노드로 SSH 가능
2. inventory.ini 최신 상태
3. ansible all -m ping 성공
4. apt lock 없음
5. 주요 포트 충돌 없음
6. 서버 시간대 KST 설정
7. 백업 저장소 접근 가능
8. 실행 대상 Playbook 문법 검사 완료
```

문법 검사 명령:

```bash
ansible-playbook -i inventory.ini <playbook>.yml --syntax-check
```

---

## 10. 멘토링 설명 기준

```text
Pre-run Checklist는 Ansible 실행 전 환경 불일치를 줄이기 위한 문서입니다.

특히 SSH, Inventory, 포트, 시간대, 백업 저장소, OpenStack 인증 정보를 사전에 확인하여 실행 실패 가능성을 줄이는 것을 목표로 합니다.
```
