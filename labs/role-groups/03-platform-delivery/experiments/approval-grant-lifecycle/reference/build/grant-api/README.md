# grant-api MVP

On-Prem control-db에서 Grant 원본과 발급·회수·만료 감사 이벤트를 관리한다. 보호 자원 접근 때 JWT 서명뿐 아니라 서버 측 Grant 상태를 다시 확인하므로 회수 전 토큰도 즉시 403으로 차단된다.

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://grant_app:<password>@<host>:5432/control_db'
$env:GRANT_SIGNING_KEY = '<secret-manager-value>'
$env:AUTO_CREATE_SCHEMA = 'true' # 로컬 MVP에서만
$env:AUTH_MODE = 'dev'           # 로컬 MVP에서만
uvicorn grant_api.main:app --app-dir services/grant-api --port 8002
```

MVP는 HS256을 사용한다. 실제망 전환 전 KMS/Vault로 보호되는 비대칭 서명키와 rotation 절차로 교체한다.
