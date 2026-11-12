# PostgreSQL schema and least privilege

운영 PostgreSQL 서버에는 논리 DB `request_db`, `control_db`, `identity_db`를 분리한다. API의
`AUTO_CREATE_SCHEMA`는 사용하지 않고 request/control은 Alembic migrator가 생성한다. `identity_db`는
Keycloak 전용이며 Keycloak이 자체 테이블을 마이그레이션한다. 서비스 API는 identity DB를 조회하지 않고
OIDC `sub`만 업무 데이터에 저장한다. request-db와 control-db는 직접 복제하지 않으며 API callback만 사용한다.

## Bootstrap order

관리 계정으로 role을 먼저 생성한다. 이 스크립트에는 password가 없으며 실제 credential은 승인된 Secret workflow에서 별도로 설정한다.

```bash
psql -v ON_ERROR_STOP=1 -d postgres -f database/roles/00-create-roles.sql
```

Migration은 각각 `request_migrator`, `control_migrator`로 실행한다. DML grant 스크립트는 테이블이 생성된 뒤 적용한다.

```bash
DATABASE_URL='postgresql+psycopg://request_migrator@<postgres-host>/request_db?sslmode=verify-full&sslrootcert=<ca>' \
  alembic -c database/migrations/request-db/alembic.ini upgrade head

DATABASE_URL='postgresql+psycopg://control_migrator@<control-db>/control_db?sslmode=verify-full&sslrootcert=<ca>' \
  alembic -c database/migrations/control-db/alembic.ini upgrade head
```

Migration 뒤 grant/default privilege를 다시 적용하고 검증한다.

```bash
psql -v ON_ERROR_STOP=1 -d request_db -f database/roles/10-request-db-grants.sql
psql -v ON_ERROR_STOP=1 -d request_db -f database/verification/verify-request-permissions.sql
psql -v ON_ERROR_STOP=1 -d control_db -f database/roles/20-control-db-grants.sql
psql -v ON_ERROR_STOP=1 -d control_db -f database/verification/verify-control-permissions.sql
psql -v ON_ERROR_STOP=1 -d identity_db -f database/schema/identity-db.sql
psql -v ON_ERROR_STOP=1 -d identity_db -f database/roles/30-identity-db-grants.sql
psql -v ON_ERROR_STOP=1 -d identity_db -f database/verification/verify-identity-permissions.sql
```

운영 app URL은 각각 `request_app`, `approval_app`, `grant_app`을 사용하고 `sslmode=verify-full`과 CA를 포함한다. migrator나 backup 계정으로 API를 실행하지 않는다.

Rollback은 migration revision별 downgrade 검토 후 수행한다. 테이블/스키마 drop이 포함된 초기 migration downgrade는 데이터 보존 dump와 명시 승인 없이 실행하지 않는다.
