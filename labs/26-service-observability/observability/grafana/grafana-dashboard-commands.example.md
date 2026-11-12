# Grafana Dashboard Command Examples

NON-PRODUCTION EXAMPLES. These references are not executed in Static mode.

```text
curl http://<grafana-server-placeholder>/api/search
curl http://<grafana-server-placeholder>/api/dashboards/uid/<dashboard-uid-placeholder>
curl http://<grafana-server-placeholder>/api/datasources
grafana dashboard import <dashboard-json-placeholder> into <dashboard-folder-placeholder>
```

The import line documents a placeholder workflow only; the validator never imports, creates, updates, or deletes dashboards. Do not add credentials, tokens, cookies, authorization headers, real UIDs, or URLs.
