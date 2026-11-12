# Istio service-mesh security overlay

최종 구조의 단일 Regional Kubernetes 내부 `user-service`와 `admin-service`에 STRICT mTLS를 적용한다.
`request-api`는 edge/mesh ingress와 하이브리드 callback gateway ServiceAccount만 호출할 수 있다.

이 overlay는 Istio CRD와 `mesh-system/mesh-ingress-gateway`가 설치된 뒤에만 적용한다. 온프레미스
PostgreSQL이나 Keycloak까지 mesh에 편입하지 않는다. 하이브리드 구간은 WireGuard/전용 연결,
서비스 OAuth audience/scope, callback allow-list로 별도 보호한다.

```bash
kubectl apply --dry-run=server -k kubernetes/security/istio
kubectl diff -k kubernetes/security/istio
kubectl apply -k kubernetes/security/istio
```

실제 적용 전 mesh 담당자는 trust domain(`cluster.local`), ingress ServiceAccount 이름, control-service가
동일 mesh 신뢰영역인지 확인해야 한다. 온프레미스 호출이 mesh principal로 보이지 않는 구성에서는
내부 callback을 별도 egress/ingress gateway에 종단하고 그 gateway principal만 허용한다.
