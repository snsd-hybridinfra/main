# Prometheus Target Discovery Validation

This baseline validates scrape-job definitions and sanitized target-health evidence without contacting Prometheus in Static mode.

## Purpose and Scrape Model

`<prometheus-server>` discovers infrastructure, service, and probe exporters through static target placeholders or `<kubernetes-service-discovery-placeholder>`.

- Node exporter: `<node-exporter-target>`
- MariaDB exporter: `<mariadb-exporter-target>`
- Nginx exporter: `<nginx-exporter-target>`
- Blackbox exporter: `<blackbox-exporter-target>`
- Job identity: `<scrape-job-name>`
- Evidence root: `<evidence-path>`

Static jobs use symbolic `static_configs` targets. Kubernetes discovery is represented by a non-production `kubernetes_sd_configs` placeholder without an API endpoint, token, or TLS credential.

## Health Expectations

- Required discovered targets must be `UP` (`health: up`).
- Required `up` query series must equal `1`.
- `DOWN`, missing required jobs, or `up = 0` is a failure in required healthy evidence unless a target is explicitly documented as intentionally disabled.
- Missing noncritical labels may be WARN according to the rule matrix; the required `job` label is mandatory.

## Evidence Collection Model

Static validation parses repository configuration and sanitized samples. Optional live Prometheus API validation runs only with `-LivePrometheus -PrometheusUrl`. It queries target and `up` endpoints without credentials/cookies/authorization, retains only required job names and health judgments, and never writes the URL, scrape targets, raw labels, or raw API response.

Static mode performs no Prometheus query or network request. Live mode is explicit and does not start, reload, or modify Prometheus.
