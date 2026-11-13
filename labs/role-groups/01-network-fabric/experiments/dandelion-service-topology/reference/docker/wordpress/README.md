<!-- STATUS: COMPLETE -->

# Custom WordPress Image

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트에서 사용하는 Custom WordPress Image의 목적, 구성 방식, 검증 기준을 정의한다.

본 프로젝트에서 WordPress는 웹 개발 대상이 아니라, OpenStack 기반 인프라 위에서 Ansible 자동화, Docker Compose 배포, HAProxy Reverse Proxy, MariaDB 연결, 상태 점검, 백업 및 복구 검증을 수행하기 위한 서비스 대상이다.

---

## 2. 프로젝트 내 역할

Custom WordPress Image는 Phase 1 필수 구성에서 Web Node에 배포된다.

~~~text
Client
→ Proxy Node / HAProxy HTTP Reverse Proxy
→ Web Node / Custom WordPress Container
→ DB Node / MariaDB Service
~~~

WordPress는 다음 검증을 위해 사용한다.

| 검증 항목 | 목적 |
|---|---|
| HTTP Service | Proxy Node 경유 HTTP 접속 확인 |
| Container Deployment | Docker Compose 기반 서비스 배포 확인 |
| DB Connection | Web Node에서 DB Node MariaDB 연결 확인 |
| Health Check | 서비스 응답 상태 확인 |
| Backup | WordPress files archive 생성 |
| Restore | WordPress files 복구 절차 검증 |

---

## 3. 이미지 기준

| 항목 | 값 |
|---|---|
| Base Image | wordpress:php8.2-apache |
| Runtime | Docker / Docker Compose |
| Deploy Target | Web Node |
| DB Target | DB Node MariaDB |
| Proxy Access | Proxy Node HAProxy 경유 |
| Project Role | 인프라 자동화 검증용 서비스 이미지 |

---

## 4. 파일 구성

권장 디렉터리 구조는 다음과 같다.

~~~text
docker/wordpress/
├── Dockerfile
├── custom.ini
└── README.md
~~~

---

## 5. Dockerfile 기준

예시 Dockerfile:

~~~dockerfile
FROM wordpress:php8.2-apache

COPY custom.ini /usr/local/etc/php/conf.d/custom.ini

LABEL project="Dandelion"
LABEL service="custom-wordpress"
LABEL base_image="wordpress:php8.2-apache"
LABEL description="Custom WordPress image for Ansible-based cloud infrastructure automation project"
~~~

---

## 6. PHP 설정 기준

예시 `custom.ini`:

~~~ini
upload_max_filesize=64M
post_max_size=64M
memory_limit=256M
max_execution_time=300
~~~

이 설정은 WordPress 운영 품질을 고도화하기 위한 목적보다는, Custom Image를 구성했다는 근거와 컨테이너 설정 변경 가능성을 보여주기 위한 기준이다.

---

## 7. Docker Compose 연동 기준

Custom WordPress Image는 Web Node의 Docker Compose에서 사용한다.

예시 구조:

~~~text
docker/compose/web/docker-compose.yml
~~~

예시 Compose 구성:

~~~yaml
services:
  wordpress:
    build:
      context: ../../wordpress
      dockerfile: Dockerfile
    container_name: dandelion-wordpress
    restart: unless-stopped
    ports:
      - "80:80"
    environment:
      WORDPRESS_DB_HOST: DB_NODE_PRIVATE_IP:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress_password
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wordpress_data:/var/www/html

volumes:
  wordpress_data:
~~~

`DB_NODE_PRIVATE_IP`는 실제 DB Node의 Private IP로 변경한다.

---

## 8. DB 연결 기준

WordPress는 Web Node 내부 DB를 사용하지 않고 DB Node의 MariaDB에 연결한다.

~~~text
Web Node
→ Custom WordPress Container
→ DB Node:3306
→ MariaDB Service
~~~

필수 환경변수:

| 환경변수 | 설명 |
|---|---|
| WORDPRESS_DB_HOST | DB Node Private IP와 3306 포트 |
| WORDPRESS_DB_USER | MariaDB WordPress 사용자 |
| WORDPRESS_DB_PASSWORD | MariaDB WordPress 사용자 비밀번호 |
| WORDPRESS_DB_NAME | WordPress 데이터베이스 이름 |

실제 비밀번호는 공개 문서나 발표자료에 그대로 노출하지 않는다.

---

## 9. Web Node 검증 기준

Web Node에서 다음 항목을 확인한다.

~~~bash
docker ps
sudo ss -tulnp | grep ':80'
curl -I http://localhost
curl -I http://WEB_NODE_PRIVATE_IP
docker logs dandelion-wordpress --tail 50
~~~

성공 기준:

| 항목 | 기준 |
|---|---|
| Image Build | Custom WordPress Image build 성공 |
| Container | dandelion-wordpress running |
| Port | Web Node 80 listening |
| HTTP | localhost 또는 Web Node IP에서 HTTP 응답 |
| DB | DB Node MariaDB 연결 성공 |
| Logs | 치명적 오류 없음 |

---

## 10. Proxy 경유 검증 기준

사용자는 Web Node에 직접 접근하지 않고 Proxy Node의 HAProxy를 통해 WordPress에 접근한다.

~~~text
Client
→ Proxy Node:80
→ HAProxy
→ Web Node:80
→ WordPress
~~~

Proxy Node 또는 외부 Client에서 확인한다.

~~~bash
curl -I http://PROXY_NODE_IP
~~~

브라우저에서는 다음 주소로 확인한다.

~~~text
http://PROXY_NODE_IP
~~~

성공 기준:

| 항목 | 기준 |
|---|---|
| Proxy | HAProxy가 Web Node로 요청 전달 |
| Web | WordPress 화면 표시 |
| HTTP | 정상 응답 확인 |
| Security | Web Node 직접 공개보다 Proxy 경유 구조 우선 |

---

## 11. Backup 대상 기준

WordPress files는 Phase 1 백업 대상이다.

백업 대상 경로:

~~~text
/var/www/html
~~~

백업 결과물 예시:

~~~text
wordpress_files.tar.gz
~~~

Backup / Validation Node에서 `backup.sh`를 통해 WordPress files archive를 생성한다.

---

## 12. Restore 대상 기준

복구 절차는 `restore.md` 기준으로 검증한다.

복구 대상:

| 항목 | 기준 |
|---|---|
| WordPress files | wordpress_files.tar.gz |
| WordPress DB | wordpress_db.sql |
| Restore Guide | restore.md |

복구 검증 시 기존 데이터를 덮어쓸 수 있으므로, 테스트 환경에서만 수행하거나 절차 검증 중심으로 진행한다.

---

## 13. Phase 2 확장 가능 항목

Phase 2에서 다음 항목을 추가할 수 있다.

| 항목 | 설명 |
|---|---|
| HTTPS | Proxy Node HAProxy에서 처리 |
| Monitoring | cAdvisor로 WordPress Container metric 수집 |
| Backup Playbook | WordPress files backup을 Ansible Playbook으로 실행 |
| Validation Report | WordPress 응답, 로그, 백업 결과를 상세 검증 문서에 반영 |

---

## 14. Phase 3 확장 시 주의사항

Phase 3에서 Web Node 2대를 구성할 경우, WordPress files 동기화 문제가 발생할 수 있다.

~~~text
Web Node 1 / WordPress files
Web Node 2 / WordPress files
DB Node / Common MariaDB
~~~

이번 프로젝트에서는 다음 항목을 제외한다.

~~~text
WordPress files 자동 동기화
wp-content/uploads 공유
plugin/theme 동기화
NFS 기반 WordPress shared storage
Object Storage 연동
DB Replication
DB Clustering
~~~

Phase 3 검증은 HAProxy roundrobin, Web-1/Web-2 응답 분산, 공통 DB Node 연결 확인 수준으로 제한한다.

---

## 15. 캡처 기준

| 캡처 항목 | 경로 예시 |
|---|---|
| Dockerfile | screenshots/web/wordpress-dockerfile.png |
| Custom Image Build | screenshots/web/custom-wordpress-build.png |
| WordPress Container | screenshots/web/wordpress-container.png |
| Web Node Port | screenshots/web/wordpress-port.png |
| DB Connection | screenshots/db/web-to-db-connection.png |
| Proxy Access | screenshots/proxy/proxy-http-result.png |
| Backup Files | screenshots/backup/wordpress-files-archive.png |

---

## 16. 핵심 메시지

~~~text
Custom WordPress Image는 웹 개발 결과물이 아니라,
인프라 자동화 프로젝트의 서비스 검증 대상이다.

Web Node에서 WordPress를 실행하고,
DB Node의 MariaDB에 연결하며,
Proxy Node의 HAProxy를 통해 외부 접속을 검증한다.

이후 WordPress files 백업과 Restore 절차를 통해
서비스 운영 검증 흐름을 완성한다.
~~~



