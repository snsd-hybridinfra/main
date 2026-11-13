# PostgreSQL logical backup and Restic

request-db, control-db, identity-db는 각각 최소권한 backup role로 `pg_dump` custom format을 생성하고 SHA-256을 계산한 뒤 Restic repository에 저장한다. dump는 업무/Keycloak schema를 포함하고 owner/privilege는 제외한다.

## Rocky Linux 9 install

```bash
sudo useradd --system --home-dir /var/lib/iaas-backup --create-home --shell /sbin/nologin iaas-backup
sudo install -d -o iaas-backup -g iaas-backup -m 0700 /var/lib/iaas-backup/staging /var/lib/iaas-backup/verification /var/cache/iaas-restic
sudo install -d -o root -g iaas-backup -m 0750 /etc/iaas-backup
sudo install -o root -g iaas-backup -m 0640 backup/restic/repository.env.example /etc/iaas-backup/common.env
sudo install -o root -g iaas-backup -m 0640 backup/restic/request-db.env.example /etc/iaas-backup/request-db.env
sudo install -o root -g iaas-backup -m 0640 backup/restic/control-db.env.example /etc/iaas-backup/control-db.env
sudo install -o root -g iaas-backup -m 0640 backup/restic/identity-db.env.example /etc/iaas-backup/identity-db.env
sudo install -o root -g root -m 0600 backup/restic/maintenance.env.example /etc/iaas-backup/maintenance.env
sudo install -o root -g iaas-backup -m 0640 <approved-postgresql-ca> /etc/iaas-backup/postgresql-ca.pem
sudo install -o root -g iaas-backup -m 0600 <approved-pgpass> /etc/iaas-backup/request-db.pgpass
sudo install -o root -g iaas-backup -m 0600 <approved-control-pgpass> /etc/iaas-backup/control-db.pgpass
sudo install -o root -g root -m 0600 <approved-backup-restic-key> /etc/iaas-backup/restic-backup-password
sudo install -o root -g root -m 0600 <approved-maintenance-restic-key> /etc/iaas-backup/restic-maintenance-password
sudo install -o root -g root -m 0600 <approved-append-only-rest-url-file> /etc/iaas-backup/restic-backup-repository
sudo install -o root -g root -m 0600 <approved-full-access-rest-url-file> /etc/iaas-backup/restic-maintenance-repository
sudo install -o root -g root -m 0644 backup/systemd/*.service backup/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now iaas-request-db-backup.timer iaas-control-db-backup.timer iaas-identity-db-backup.timer iaas-restic-maintenance.timer
```

설치한 예시 환경 파일의 endpoint와 DB 식별자는 운영값으로 수정한다. 실제 credential 파일 내용은 Git에 저장하지 않는다. `.pgpass` 형식은 `host:port:database:user:password`다.

`restic-backup-repository`는 삭제·덮어쓰기가 차단된 append-only REST URL/account만 담는다. `restic-maintenance-repository`는 `forget/prune` 가능한 별도 URL/account이며 root 외에는 읽을 수 없어야 한다. 두 Restic key는 동일 repository master key를 여는 별도 key로 발급하고, 일일 백업 unit에는 maintenance URL과 key를 전달하지 않는다. URL 파일은 Restic이 공식 지원하는 `RESTIC_REPOSITORY_FILE`로만 주입하므로 REST 서버 비밀번호가 unit 환경 파일이나 명령행에 노출되지 않는다.

## Verification

```bash
sudo systemctl start iaas-request-db-backup.service
sudo journalctl -u iaas-request-db-backup.service --since today --no-pager
sudo systemctl start iaas-backup-verify@request-db.service
sudo systemctl start iaas-backup-verify@control-db.service
sudo journalctl -u 'iaas-backup-verify@*.service' --since today --no-pager
sudo systemctl start iaas-backup-append-only-test.service
sudo journalctl -u iaas-backup-append-only-test.service --since today --no-pager
sudo systemctl start iaas-restic-maintenance.service
```

snapshot 존재 확인만으로 완료 처리하지 않는다. checksum, `pg_restore --list`, 격리 DB 복원까지 통과해야 한다. 일일 백업은 append-only endpoint로 snapshot 생성만 수행하며, canary 삭제 시도가 HTTP 403/권한 거부인지 운영 투입 시 한 번 검증한다. 두 DB의 `keep-within` retention은 격리된 주간 유지보수 credential로 순차 적용한 뒤 `prune`과 repository data subset 검사를 각각 한 번 수행한다. 백업과 유지보수는 공용 파일 잠금으로 직렬화한다.

Rollback은 timer를 중지하고 직전 스크립트/설정을 복원하는 방식이다. 이미 생성된 정상 snapshot을 rollback 과정에서 삭제하지 않는다.
