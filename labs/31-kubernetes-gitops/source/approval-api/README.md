# approval-api on k3s

zero digest, request-api private DNS, control-db IP, Keycloak JWKS URL과 CIDR placeholder를 실제 인수값으로 교체한다. Keycloak 자체 설정은 조장 소유다.

`approval-api-runtime`, `approval-api-oauth`, `control-db-migrator`, `service-trust-bundle`은 Git 밖의 secret provider가 만든다. approval API는 `approval_app`, migration은 `control_migrator` DB 계정을 사용한다.

```bash
kubectl create -f kubernetes/approval-api/migration-job.yaml
kubectl -n control-service wait --for=condition=complete job -l app.kubernetes.io/name=control-db-migration --timeout=5m
kubectl apply --dry-run=server -k kubernetes/approval-api
kubectl diff -k kubernetes/approval-api
kubectl apply -k kubernetes/approval-api
kubectl -n control-service rollout status deploy/approval-api --timeout=5m
```

DB downgrade는 별도 승인 대상이며 Deployment rollback은 직전 digest를 재적용한다.
