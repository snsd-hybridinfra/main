<!-- STATUS: CURRENT -->

# Provisioning Playbook Design

## 1. 문서 목적

본 문서는 OpenStack 인스턴스 생성 자동화를 위한 Provisioning Playbook 설계 기준을 정리한다.

프로젝트의 최종 목표는 Control Node에서 Ansible Playbook을 실행하여 OpenStack 인스턴스 생성부터 서비스 구성, 모니터링, 백업 및 복구 검증까지 자동화하는 것이다.

현재는 생성된 인스턴스를 대상으로 구성 자동화와 운영 자동화를 우선 구현하였으며, 본 문서는 최종 목표 달성을 위한 `provision.yml` 설계 기준을 정의한다.

---

## 2. Provisioning 자동화 목표

Provisioning 자동화의 목표는 다음과 같다.

```text
Control Node
→ Ansible OpenStack Module 실행
→ Security Group 생성
→ Instance 생성
→ Floating IP 연결
→ Cinder Volume 생성
→ Volume Attach
→ Inventory 생성 또는 갱신
→ SSH 가능 상태 확인
```

---

## 3. 자동화 대상 리소스

| 리소스 | 설명 | 자동화 필요 여부 |
|---|---|---|
| Instance | Control, Proxy, Web, DB, Monitoring, Backup Node 생성 | 필요 |
| Security Group | SSH, HTTP, HTTPS, Monitoring, DB 포트 제어 | 필요 |
| Security Group Rule | 서비스별 허용 포트 정의 | 필요 |
| Floating IP | 외부 접근용 IP 연결 | 필요 |
| Cinder Volume | Backup / Recovery Node 백업 저장소 | 필요 |
| Server Volume Attach | Backup Node에 Cinder Volume 연결 | 필요 |
| Inventory | 생성된 인스턴스 IP 기반 관리 대상 정의 | 필요 |
| SSH Wait | 인스턴스 생성 후 접속 가능 상태 확인 | 필요 |

---

## 4. 사용 예정 Ansible Collection

OpenStack Provisioning에는 다음 Collection 사용을 기준으로 한다.

```text
openstack.cloud
```

설치 예시:

```bash
ansible-galaxy collection install openstack.cloud
```

Python SDK 확인:

```bash
python3 -c "import openstack"
```

필요 시 설치:

```bash
pip3 install openstacksdk
```

---

## 5. 사용 예정 모듈

| 모듈 | 목적 |
|---|---|
| openstack.cloud.server | 인스턴스 생성 |
| openstack.cloud.security_group | 보안그룹 생성 |
| openstack.cloud.security_group_rule | 보안그룹 Rule 생성 |
| openstack.cloud.volume | Cinder Volume 생성 |
| openstack.cloud.server_volume | 인스턴스에 Volume 연결 |
| openstack.cloud.floating_ip | Floating IP 생성 또는 연결 |
| openstack.cloud.port_info | Port 정보 조회 |
| openstack.cloud.server_info | 인스턴스 정보 조회 |

---

## 6. 최소 구현 범위

남은 기간을 고려하여 Provisioning Playbook의 최소 구현 범위는 다음으로 제한한다.

```text
1. Security Group 생성
2. Security Group Rule 생성
3. Proxy / Web / DB / Monitoring / Backup Node 생성
4. Backup용 Cinder Volume 생성
5. Backup Node에 Volume Attach
6. 생성된 인스턴스 IP 출력
7. SSH 접속 가능 상태 확인
```

Control Node는 Playbook 실행 지점이므로, 실제 환경에 따라 자동 생성 대상에서 제외할 수 있다.

---

## 7. 권장 변수 구조

`group_vars/all.yml` 또는 `vars/provisioning.yml`에 다음 변수를 정의한다.

```yaml
openstack_cloud: dandelion

default_image: ubuntu-22.04
default_key_name: dandelion-key
default_network: private-network
default_flavor: m1.small

instances:
  - name: proxy-node
    role: proxy
    flavor: m1.small
    volume_size: 15
  - name: web-node
    role: web
    flavor: m1.small
    volume_size: 20
  - name: db-node
    role: db
    flavor: m1.medium
    volume_size: 20
  - name: monitoring-node
    role: monitoring
    flavor: m1.small
    volume_size: 15
  - name: backup-node
    role: backup
    flavor: m1.small
    volume_size: 20

backup_volume:
  name: backup-volume
  size: 80
  target_server: backup-node
```

실제 Flavor, Image, Network 이름은 OpenStack 실습 환경 기준으로 변경한다.

---

## 8. provision.yml 설계 예시

아래는 설계용 예시이며, 실제 실행 전 환경 변수와 리소스 이름을 반드시 확인한다.

```yaml
---
- name: Provision OpenStack infrastructure
  hosts: localhost
  connection: local
  gather_facts: false

  vars_files:
    - vars/provisioning.yml

  tasks:
    - name: Create security group
      openstack.cloud.security_group:
        cloud: "{{ openstack_cloud }}"
        state: present
        name: dandelion-sg
        description: Dandelion project security group

    - name: Allow SSH
      openstack.cloud.security_group_rule:
        cloud: "{{ openstack_cloud }}"
        security_group: dandelion-sg
        protocol: tcp
        port_range_min: 22
        port_range_max: 22
        remote_ip_prefix: 0.0.0.0/0

    - name: Allow HTTP
      openstack.cloud.security_group_rule:
        cloud: "{{ openstack_cloud }}"
        security_group: dandelion-sg
        protocol: tcp
        port_range_min: 80
        port_range_max: 80
        remote_ip_prefix: 0.0.0.0/0

    - name: Create instances
      openstack.cloud.server:
        cloud: "{{ openstack_cloud }}"
        state: present
        name: "{{ item.name }}"
        image: "{{ default_image }}"
        key_name: "{{ default_key_name }}"
        flavor: "{{ item.flavor | default(default_flavor) }}"
        network: "{{ default_network }}"
        security_groups:
          - dandelion-sg
        wait: true
        timeout: 300
      loop: "{{ instances }}"
      register: created_servers

    - name: Create backup volume
      openstack.cloud.volume:
        cloud: "{{ openstack_cloud }}"
        state: present
        name: "{{ backup_volume.name }}"
        size: "{{ backup_volume.size }}"

    - name: Attach backup volume
      openstack.cloud.server_volume:
        cloud: "{{ openstack_cloud }}"
        state: present
        server: "{{ backup_volume.target_server }}"
        volume: "{{ backup_volume.name }}"

    - name: Print created server information
      ansible.builtin.debug:
        var: created_servers
```

---

## 9. wait-ssh.yml 설계 예시

```yaml
---
- name: Wait for SSH on provisioned nodes
  hosts: all
  gather_facts: false

  tasks:
    - name: Wait for SSH port
      ansible.builtin.wait_for:
        host: "{{ ansible_host }}"
        port: 22
        timeout: 300
        state: started
      delegate_to: localhost

    - name: Check Ansible ping
      ansible.builtin.ping:
```

---

## 10. Inventory 자동화 방향

Provisioning 이후 Inventory 자동화는 두 방식 중 하나로 선택한다.

### 10.1 정적 Inventory 갱신

생성된 인스턴스의 IP를 확인한 뒤 `inventory.ini`를 갱신한다.

장점:

```text
구현이 단순하다.
학원 프로젝트에서 검증하기 쉽다.
```

단점:

```text
완전 자동화 수준은 낮다.
IP 변경 시 수동 수정이 필요하다.
```

### 10.2 동적 Inventory 사용

OpenStack Dynamic Inventory를 사용한다.

장점:

```text
OpenStack 인스턴스 정보를 자동으로 반영할 수 있다.
Provisioning 자동화와 잘 맞는다.
```

단점:

```text
설정 난도가 높다.
멘토링 전 짧은 기간에 실패 가능성이 있다.
```

남은 기간을 고려하면 1차 목표는 정적 Inventory 갱신 방식으로 두고, 가능하면 동적 Inventory를 확장 방향으로 문서화한다.

---

## 11. 검증 기준

Provisioning Playbook 성공 기준은 다음과 같다.

| 검증 항목 | 성공 기준 |
|---|---|
| Security Group | 생성 확인 |
| Security Group Rule | SSH / HTTP 등 필요한 Rule 확인 |
| Instance | 모든 대상 노드 Active |
| Floating IP | 지정 대상에 연결 |
| Cinder Volume | backup-volume 생성 |
| Volume Attach | Backup Node에 연결 |
| SSH Wait | 모든 노드 SSH 가능 |
| Ansible Ping | 모든 노드 pong 응답 |
| Inventory | 실제 IP와 문서 IP 일치 |

---

## 12. 멘토링 답변 기준

멘토링에서 Provisioning 자동화에 대해 질문받으면 다음 기준으로 답변한다.

```text
최종 목표는 Control Node에서 Ansible Playbook을 실행하여 OpenStack 인스턴스 생성부터 서비스 구성까지 연결하는 것입니다.

현재는 생성된 인스턴스 기반의 구성 자동화와 운영 검증 자동화를 먼저 구현했으며,
Provisioning 자동화는 provision.yml로 분리하여 보완하고 있습니다.

남은 기간에는 Security Group, Instance 생성, Volume Attach, SSH Wait까지를 최소 범위로 구현하고,
동적 Inventory는 확장 방향으로 문서화할 예정입니다.
```

---

## 13. 결론

Provisioning Playbook은 프로젝트 제목의 “클라우드 인프라 자동화”를 직접적으로 증명하는 핵심 보완 범위이다.

최소 구현 범위는 다음으로 고정한다.

```text
Security Group
→ Instance
→ Volume
→ Attach
→ SSH Wait
→ Inventory
```

이 범위만 구현해도 최종 발표에서 다음 흐름을 설명할 수 있다.

```text
Control Node에서 Ansible 실행
→ OpenStack 리소스 생성
→ 서버 구성 자동화
→ 서비스 배포
→ 모니터링
→ 백업 / 복구 검증
```
