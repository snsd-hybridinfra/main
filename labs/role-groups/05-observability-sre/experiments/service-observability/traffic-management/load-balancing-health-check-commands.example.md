# Load Balancing Health Check Command Examples

NON-PRODUCTION EXAMPLES. These are documentation only and are not run by Static validation.

```text
curl -I http://<load-balancer-placeholder>/<backend-health-path-placeholder>
curl http://<backend-service-a-placeholder>/<backend-health-path-placeholder>
curl http://<backend-service-b-placeholder>/<backend-health-path-placeholder>
tail -n 100 <load-balancer-access-log-placeholder>
tail -n 100 <load-balancer-error-log-placeholder>
```

Do not add real domains, addresses, machine-specific paths, credentials, cookies, tokens, authorization headers, or TLS material.
