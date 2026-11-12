# grant-api on k3s

zero digest, request-api private DNS, control-db IP, Keycloak JWKS/OAuth URL과 CIDR placeholder를 실제 인수값으로 교체한다. `grant-api-runtime`, `grant-api-oauth`, `grant-expiry-oauth`, `service-trust-bundle`, `grant-signing-keys`는 external secret provider가 생성한다.

`grant-expiry` CronJob은 5분마다 별도 client-credentials(`service` role, `grant:write` scope)로 만료 API를 호출한다. 동시 실행은 `Forbid`하며 API Pod와 DB에 직접 접근하지 않는다.

운영 Grant JWT는 `RS256`이며 private key는 grant-api만 읽는다. public key와 issuer/audience는 보호 자원 검증자에게 별도 계약으로 전달한다. HS256은 로컬 MVP 전용이다.

```bash
kubectl apply --dry-run=server -k kubernetes/grant-api
kubectl diff -k kubernetes/grant-api
kubectl apply -k kubernetes/grant-api
kubectl -n control-service rollout status deploy/grant-api --timeout=5m
```

Rollback은 직전 image digest와 ConfigMap을 재적용한다. signing key rollback은 이미 발급된 token 검증 기간과 rotation 절차를 함께 검토한다.
