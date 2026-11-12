# Grafana Dashboard Validation

This baseline validates non-production dashboard artifacts and sanitized API evidence without contacting Grafana in Static mode.

## Dashboard Model

- Grafana server: `<grafana-server>`
- Prometheus datasource: `<prometheus-datasource-placeholder>`
- Dashboard title: `<dashboard-title>`
- Folder: `<dashboard-folder-placeholder>`
- Panel/query: `<panel-title>` with `<promql-placeholder>`
- Evidence: `<evidence-path>`

The required dashboard covers infrastructure/Prometheus targets, Kubernetes nodes and Pods, MariaDB replication threads and lag, Nginx reverse proxy health, load-balancer health, Blackbox probe success, and overall service availability. An `<alert-readiness-placeholder>` documents future alert readiness without provisioning alerts.

## Evidence Model

Static validation parses the datasource YAML, dashboard JSON, rule matrix, commands, and sanitized samples. Optional LiveGrafana validation runs only with `-LiveGrafana -GrafanaUrl`, queries unauthenticated search/datasource endpoints, and retains only the requested placeholder title, panel-count judgment, known datasource name, and timestamp.

retired-numbered-case owns anonymous-access denial. A live 401/403 is WARN. retired-numbered-case owns Prometheus target discovery; retired-numbered-case validates only dashboard definitions and visibility coverage.
