# Kubernetes security baseline

이 Kustomization은 본 역할의 `edge-system`, `user-service`만 생성하고 Pod Security `restricted`와 default deny를 적용한다. 공용 `system` namespace는 cluster ingress controller·Alloy 등 다른 담당 workload를 깨뜨릴 수 있어 여기서 변경하지 않는다.

`10.20.0.0/16`, `10.20.10.0/24`, `10.10.0.0/16`은 저장소의 OpenStack tenant, 검증 subnet, 내부 서비스 계획 범위다. 이 매니페스트는 구성 후보이며 실제 배포 전 Zero Trust 네트워크 담당자의 검토가 필요하다.

```bash
kubectl kustomize kubernetes/security
kubectl apply --dry-run=server -k kubernetes/security
kubectl diff -k kubernetes/security
kubectl apply -k kubernetes/security
```

Rollback은 이전 승인 revision을 다시 적용한다. default-deny만 단독 삭제하는 rollback은 금지한다.

서비스 메시 정책은 Istio 설치 여부와 trust domain 협의가 필요하므로 기본 Kustomization과 분리한
[`istio`](./istio/) overlay로 제공한다.
