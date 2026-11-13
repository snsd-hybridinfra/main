# approval-api MVP

On-Prem control-db에서 승인 요청 원본, 결정, 감사 이벤트를 관리한다. 승인 시 request-api 상태 Callback과 grant-api 발급을 시도하고 실패 횟수를 기록한다.

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://approval_app:<password>@<host>:5432/control_db'
$env:AUTO_CREATE_SCHEMA = 'true' # 로컬 MVP에서만
$env:AUTH_MODE = 'dev'           # 로컬 MVP에서만
uvicorn approval_api.main:app --app-dir services/approval-api --port 8001
```
