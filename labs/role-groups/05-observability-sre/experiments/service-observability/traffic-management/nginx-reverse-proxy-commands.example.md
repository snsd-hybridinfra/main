# Nginx Reverse Proxy Command Examples

NON-PRODUCTION EXAMPLES. These commands are references only and are not executed by default validation.

```text
nginx -t -c <nginx-config-placeholder>
curl -I http://<reverse-proxy-host-placeholder>/
curl http://<reverse-proxy-host-placeholder>/<backend-health-path-placeholder>
tail -n 100 <nginx-access-log-placeholder>
tail -n 100 <nginx-error-log-placeholder>
```

Do not substitute committed domains, addresses, credentials, cookies, authorization headers, machine-specific log paths, or TLS material. Live validation is performed only through the guarded validator interface.

