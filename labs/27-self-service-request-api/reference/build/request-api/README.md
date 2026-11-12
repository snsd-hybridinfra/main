# request-api MVP

`request_db`의 `access_requests` 원본과 사용자 Projection을 관리한다.

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://request_app:<password>@<host>:5432/request_db'
$env:AUTO_CREATE_SCHEMA = 'true' # 로컬 MVP에서만
$env:AUTH_MODE = 'dev'           # 로컬 MVP에서만
uvicorn request_api.main:app --app-dir services/request-api --port 8000
```

운영에서는 `AUTO_CREATE_SCHEMA=false`, `AUTH_MODE=oidc`를 사용하고 Alembic migration을 별도 실행한다.
