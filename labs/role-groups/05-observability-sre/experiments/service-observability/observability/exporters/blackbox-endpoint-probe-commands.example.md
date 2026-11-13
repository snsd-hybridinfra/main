# Blackbox Endpoint Probe Command Examples

NON-PRODUCTION EXAMPLES. These are not executed in Static mode.

```text
curl "http://<blackbox-exporter-placeholder>:9115/probe?target=<endpoint-url-placeholder>&module=http_2xx_placeholder"
curl "http://<prometheus-server-placeholder>/api/v1/query?query=probe_success"
curl "http://<prometheus-server-placeholder>/api/v1/query?query=probe_http_status_code"
curl "http://<prometheus-server-placeholder>/api/v1/query?query=probe_duration_seconds"
```

Do not add real URLs, domains, addresses, credentials, tokens, cookies, authorization headers, or TLS material.
