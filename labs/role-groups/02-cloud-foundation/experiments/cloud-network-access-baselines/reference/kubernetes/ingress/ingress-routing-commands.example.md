# Kubernetes Ingress Routing Command Reference

NON-PRODUCTION EXAMPLES: these commands contain no real endpoint, domain, address, kubeconfig path, token, certificate, or credential.

```text
kubectl apply --dry-run=client -f kubernetes/ingress/sample-service/ingress.example.yaml
kubectl get ingress -n snsd-example
kubectl describe ingress <ingress-name> -n <namespace>
kubectl get svc -n snsd-example
kubectl get endpoints -n snsd-example
kubectl get pods -n snsd-example -l app=<app-label-placeholder>
```

Manual HTTP example only; the validator never executes curl:

```text
curl -H "Host: <host-placeholder>" http://<ingress-address-placeholder>/
```

retired-numbered-case optional live mode executes only the four read-only kubectl Ingress, Service, and Endpoints queries.
