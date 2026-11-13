# request-api on Kubernetes

배포 전 zero digest, 조장 제공 OIDC/OAuth 값, On-Prem approval URL, node taint/label을 실제 인수값으로 교체한다. `request-api-runtime`, `request-api-oauth`, `request-db-migrator`, `service-trust-bundle`은 external secret provider가 생성하며 Git에 Secret 값을 저장하지 않는다.

Migration Job은 기본 Kustomization에 포함하지 않는다. 공급망/운영 승인 단계에서 먼저 일회성으로 실행한다.

```bash
kubectl create -f kubernetes/request-api/migration-job.yaml
kubectl -n user-service wait --for=condition=complete job -l app.kubernetes.io/name=request-db-migration --timeout=5m
kubectl apply --dry-run=server -k kubernetes/request-api
kubectl diff -k kubernetes/request-api
kubectl apply -k kubernetes/request-api
kubectl -n user-service rollout status deploy/request-api --timeout=5m
```

Rollback은 Deployment 직전 revision을 재적용한다. DB downgrade는 데이터 손실 검토와 별도 승인 없이는 실행하지 않는다.
