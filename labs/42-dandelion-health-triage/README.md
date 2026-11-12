# Lab 42: Multi-Service Health Triage and Escalation

**State: `REFERENCE_EXTRACTED / NOT_REVALIDATED`.** Team Dandelion source check scripts are preserved as **non-executable text**. Do not run original commands; they include service restarts, SSH to old hosts, and potentially destructive database recovery attempts.

## Scope
- `reference/scripts/health-check/*.reference.txt`: historical Web, DB, HAProxy, Backup and Control node check logic
- `reference/scripts/health_check.sh.reference.txt`: older local diagnostic template
- `reference/docs/monitoring-plan.md`: planned Prometheus, Exporter, Grafana and Alertmanager coverage

## What to build
1. Safe **read-only** health probes: host reachability, HTTP, port check, DB replication/readiness and service target status on synthetic hosts.
2. Report `UP`, `DOWN`, `UNKNOWN`, and `NOT_CHECKED` separately, with probe timeout, false positive handling and timestamp.
3. Never repair just because ping fails. Log an explicit proposed action and approval, then test rollback in a disposable environment.
4. Add Prometheus/Blackbox exporter integration and a Grafana dashboard only after probe correctness is established.
5. Record normal, denied, failed, recovered and ambiguous connectivity outcomes.

**Not included:** working Prometheus deployment or a confirmed HAProxy configuration. The old source scripts and planning notes are not proof of readiness. Attribution: Team Dandelion, `snsd-hybridinfra/dandelion-cloud-automation@22a21c02973e696a9a07c91da3bc2ea033881ea6`.
