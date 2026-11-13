# Lab 26: Service Observability, Probes & Traffic Health

**Status:** `MIGRATED / NOT_REVALIDATED`. These are configuration, dashboard and response-matrix **examples**, not a deployed monitoring service.

## Goal
Monitor synthetic endpoints and application health with Prometheus, Blackbox Exporter and Grafana; correlate proxy/backend failures and validate alert/noise boundaries.

## Reference materials
- `observability/prometheus/`: scrape targets, alerts, failure/replication response rules
- `observability/exporters/`: Blackbox synthetic probe definitions
- `observability/grafana/`: example dashboard and access control/verification notes
- `traffic-management/`: Nginx proxy/health snippets and incident handling criteria

## Before applying
1. Replace placeholder metrics with verified real exporter names in a disposable lab; avoid copying the source dashboard's placeholder `<...>` values unchanged.
2. Review all proxy listeners, backend names and user access boundaries.
3. Reproduce target `up==0`, `probe_success==0`, HTTP status failures, and recovery with synthetic services.
4. Compare observability results with Lab 18's sanitized logs; don't claim root-cause diagnosis from metrics alone.

## Source
`snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No runtime acceptance transferred.
