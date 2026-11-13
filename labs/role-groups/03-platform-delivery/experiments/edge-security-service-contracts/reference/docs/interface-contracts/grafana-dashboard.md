# Admin Portal ↔ Grafana 대시보드 계약

소유 경계: Admin Portal의 대시보드 소비 기능은 서비스 담당, Grafana·Prometheus·Loki·Dashboard 구성과 운영은 모니터링 담당

## 현재 동작

관리자 포털은 원시 감사 이벤트를 직접 나열하지 않는다. approval-api의 다음 설정 상태를 조회한다.

```text
GET /admin-api/v1/monitoring-dashboard
```

응답 상태:

- `PENDING`: URL 미설정, 포털에 `Grafana 연동 대기` 표시
- `READY`: 유효한 URL, 포털에 iframe과 새 창 링크 자동 생성
- `INVALID`: HTTP(S) 또는 동일 출처 경로가 아닌 URL, 설정 오류 표시

원본 승인·Grant 감사 이벤트는 control-db와 기존 감사 API에 계속 기록한다. Grafana 연동 전이라도 감사 원본은 삭제하지 않는다.

## 인수 입력

모니터링 담당이 대시보드를 완성하면 서비스 배포 설정에 다음 값을 전달한다.

```text
GRAFANA_DASHBOARD_URL=https://grafana.example.com/d/iaas-operations/overview?kiosk
```

동일 Pomerium 보호 경로로 프록시한다면 `/grafana/d/...` 형식의 동일 출처 경로도 허용한다. 설정 반영 후 approval-api를 재시작하면 관리자 포털이 별도 코드 변경 없이 자동으로 대시보드를 불러온다.

## 보안 조건

- URL에 API key, service account token 또는 사용자 credential을 넣지 않는다.
- Grafana 익명 접근을 활성화하지 않는다.
- 관리자 접근은 Pomerium/Keycloak 인증 경로와 역할 정책을 따른다.
- iframe 사용 시 Grafana의 embedding 설정과 CSP `frame-ancestors`를 관리자 포털 출처로 제한한다.
- 대시보드에는 내부 request/grant/resource ID 대신 집계 지표와 마스킹된 라벨을 사용한다.
- 연결 실패는 `동기화 실패`가 아니라 별도의 `Grafana 연동 대기/설정 오류` 상태로 표시한다.

## 권장 대시보드 패널

- 승인 대기 건수
- 재시도 가능한 Callback 실패 건수
- Grant ACTIVE/REVOKED/EXPIRED 건수
- 프로비저닝 RUNNING/FAILED/TERMINATED 건수
- API 4xx/5xx, 지연시간, DB 연결 상태
- WAF 차단, 인증 실패, 백업·복구 최근 성공 시각
