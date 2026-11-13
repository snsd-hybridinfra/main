# DB Primary Stop Metrics Example

NON-PRODUCTION placeholders only:

- `mysql_up{instance="<db-primary-instance-placeholder>"}`
- `mysql_global_status_threads_connected{instance="<db-primary-instance-placeholder>"}`
- `mysql_slave_status_slave_io_running{instance="<db-replica-instance-placeholder>"}`
- `mysql_slave_status_seconds_behind_master{instance="<db-replica-instance-placeholder>"}`

retired-numbered-case does not query Prometheus and includes no real target, address, datasource, or credential.
