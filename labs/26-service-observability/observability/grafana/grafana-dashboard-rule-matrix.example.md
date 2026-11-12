# Grafana Dashboard Rule Matrix Example

NON-PRODUCTION EXAMPLE.

| Dashboard Area | Required Panel | Datasource Placeholder | Query / Metric Placeholder | Expected Visualization | Failure Condition | Evidence Reference |
|---|---|---|---|---|---|---|
| Prometheus target status | Prometheus Target Status | `<prometheus-datasource-placeholder>` | `up` | Stat | Panel/query missing | `<evidence-path>` |
| Kubernetes node readiness | Kubernetes Node Readiness | `<prometheus-datasource-placeholder>` | `kube_node_status_condition` | Stat | Panel/query missing | `<evidence-path>` |
| Kubernetes pod readiness | Kubernetes Pod Readiness | `<prometheus-datasource-placeholder>` | `kube_pod_status_ready` | Stat | Panel/query missing | `<evidence-path>` |
| Nginx reverse proxy health | Nginx Reverse Proxy Health | `<prometheus-datasource-placeholder>` | `nginx_http_requests_total` | Timeseries | Panel/query missing | `<evidence-path>` |
| Load balancing health check | Load Balancer Health | `<prometheus-datasource-placeholder>` | `load_balancer_health_placeholder` | Stat | Panel/query missing | `<evidence-path>` |
| MariaDB replication thread status | MariaDB Replication IO Thread / MariaDB Replication SQL Thread | `<prometheus-datasource-placeholder>` | `mysql_slave_status_slave_io_running` / `mysql_slave_status_slave_sql_running` | Stat | Either panel/query missing | `<evidence-path>` |
| MariaDB replication lag | MariaDB Replication Lag | `<prometheus-datasource-placeholder>` | `mariadb_replication_lag_seconds` | Timeseries | Panel/query missing | `<evidence-path>` |
| Blackbox endpoint probe | Blackbox Probe Success | `<prometheus-datasource-placeholder>` | `probe_success` | Stat | Panel/query missing | `<evidence-path>` |
| Service availability summary | Service Availability Summary | `<prometheus-datasource-placeholder>` | `up` | Stat | Panel/query missing | `<evidence-path>` |
