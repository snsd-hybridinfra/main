# Service Health After Recovery Metrics Example

NON-PRODUCTION placeholders only:

- `up{job="<scrape-job-name-placeholder>"}`
- `probe_success{instance="<blackbox-target-placeholder>"}`
- `probe_http_status_code{instance="<blackbox-target-placeholder>"}`
- `kube_deployment_status_replicas_available{deployment="<deployment-name-placeholder>"}`
- `kube_pod_status_ready{pod="<pod-name-placeholder>"}`
- `nginx_up{instance="<load-balancer-instance-placeholder>"}`
- `nginx_http_response_5xx_total{instance="<load-balancer-instance-placeholder>"}`

retired-numbered-case does not query Prometheus in Static mode and stores no real target, URL, label, address, datasource, or credential.
