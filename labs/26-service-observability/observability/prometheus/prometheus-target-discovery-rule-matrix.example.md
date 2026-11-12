# Prometheus Target Discovery Rule Matrix Example

NON-PRODUCTION EXAMPLE. Authentication material must not be committed.

| Scrape Job | Target Placeholder | Expected State | Required Labels | Failure Condition | Validation Method | Evidence Reference |
|---|---|---|---|---|---|---|
| prometheus-self-placeholder | `<prometheus-server>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |
| node-exporter-placeholder | `<node-exporter-target>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |
| mariadb-exporter-placeholder | `<mariadb-exporter-target>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |
| nginx-exporter-placeholder | `<nginx-exporter-target>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |
| blackbox-exporter-placeholder | `<blackbox-exporter-target>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |
| kubernetes-service-discovery-placeholder | `<kubernetes-service-discovery-placeholder>` | UP | `job` required; optional labels WARN | Missing, DOWN, or `up=0` | Config and sample parsing | `<evidence-path>` |

DOWN targets fail required healthy validation unless an intentionally disabled state is explicitly documented and separately reviewed.
