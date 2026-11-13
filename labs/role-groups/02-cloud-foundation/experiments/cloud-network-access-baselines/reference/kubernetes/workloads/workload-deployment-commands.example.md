# Kubernetes Workload Deployment Command Reference

NON-PRODUCTION EXAMPLES: these commands contain no endpoint, kubeconfig path, token, certificate, or credential.

```text
kubectl apply --dry-run=client -f kubernetes/namespaces/snsd-example.namespace.yaml
kubectl apply --dry-run=client -f kubernetes/workloads/sample-service/deployment.example.yaml
kubectl apply --dry-run=client -f kubernetes/workloads/sample-service/service.example.yaml
kubectl get deployments -n snsd-example
kubectl get pods -n snsd-example
kubectl describe deployment <deployment-name> -n <namespace>
kubectl rollout status deployment/<deployment-name> -n <namespace>
```

retired-numbered-case optional live mode executes only the two `get` commands. Dry-run, describe, and rollout commands are documentation examples and are not invoked by the validator.
