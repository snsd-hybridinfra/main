# edge-gateway on Kubernetes

이 Manifest는 기존 NLB를 새로 만들지 않는다. `NodePort 30443`을 제공하고 OpenStack 인프라·Terraform 담당자가 기존 NLB TCP 443 target group에 연결한다. IP target/TargetGroupBinding 방식을 선택했다면 OpenStack 인프라·Terraform 담당이 제공한 target group ARN에 맞춘 별도 승인 patch가 필요하다.

배포 전 반드시 교체할 값:

- image의 64자리 zero digest → 공급망에서 서명·검증된 digest
- `approval-api.control.internal`, `grant-api.control.internal` → On-Prem/WireGuard private DNS
- `keycloak.control.internal` → 조장이 제공한 Keycloak upstream/SNI
- `edge-gateway-tls`, `edge-upstream-ca` → 승인된 external secret provider로 생성
- node label/taint와 `30443` target 계약 → OpenStack 인프라 담당 확인

Pomerium configuration은 이 경로에 포함하지 않는다. Zero Trust 접근 담당자가 route/policy를 관리한다.

```bash
kubectl kustomize kubernetes/edge-gateway
kubectl apply --dry-run=server -k kubernetes/edge-gateway
kubectl diff -k kubernetes/edge-gateway
kubectl apply -k kubernetes/edge-gateway
kubectl -n edge-system rollout status deploy/edge-gateway --timeout=5m
```

Rollback:

```bash
kubectl -n edge-system rollout undo deploy/edge-gateway
kubectl -n edge-system rollout status deploy/edge-gateway --timeout=5m
```
