# DB Replication Lag Metric Examples

NON-PRODUCTION METRIC EXAMPLES. Names may vary by exporter version and must be verified before any lab use.

- `mysql_slave_status_seconds_behind_master`
- `mariadb_replication_lag_seconds`
- `mysql_slave_status_slave_io_running`
- `mysql_slave_status_slave_sql_running`

Use only symbolic labels such as `<db-replica-host>` and `<replication-channel>`. This file contains no Prometheus URL, scrape target, database connection, credential, or production label.

Live Prometheus target discovery is handled in retired-numbered-case. Grafana dashboard validation is handled in retired-numbered-case. retired-numbered-case performs no Prometheus or Grafana query.
