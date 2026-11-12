# Kubernetes Node Readiness Command Reference

NON-PRODUCTION EXAMPLES: run only in a separately approved environment. These commands contain no endpoint, node address, kubeconfig path, token, or certificate.

```text
kubectl get nodes
kubectl get nodes -o wide
kubectl describe node <node-name>
kubectl get node <node-name> -o jsonpath='{.status.conditions}'
kubectl get --raw='/readyz?verbose'
```

retired-numbered-case optional live mode deliberately uses only `kubectl get nodes --no-headers`; the broader commands above are documentation references and are not executed by the validator.
