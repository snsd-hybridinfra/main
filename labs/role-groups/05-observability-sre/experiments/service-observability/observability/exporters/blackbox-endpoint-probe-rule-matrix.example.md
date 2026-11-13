# Blackbox Endpoint Probe Rule Matrix Example

NON-PRODUCTION EXAMPLE.

| Probe Area | Required Metric | Expected Value / Range | Operational Judgment | Failure Condition | Validation Method | Evidence Reference |
|---|---|---|---|---|---|---|
| Probe success | `probe_success` | `1` | HEALTHY | `0` | Sample parsing | `<evidence-path>` |
| HTTP status | `probe_http_status_code` | `200` or `204` | HEALTHY | `0`, 5xx, or unexpected | Sample parsing | `<evidence-path>` |
| Probe duration | `probe_duration_seconds` | `<=2.0` normal; `>2.0..5.0` warning | NORMAL/WARNING | `>5.0` | Sample parsing | `<evidence-path>` |
| DNS lookup duration placeholder | `probe_dns_lookup_time_seconds` | `<probe-duration-threshold-seconds>` | OBSERVED | Metric missing | Documentation review | `<evidence-path>` |
| Connect duration placeholder | `probe_connect_duration_seconds` | `<probe-duration-threshold-seconds>` | OBSERVED | Metric missing | Documentation review | `<evidence-path>` |
| HTTP timeout | timeout indicator | `<probe-timeout-seconds>` | FAILURE | Timeout present | Sample parsing | `<evidence-path>` |
| TCP connect failure | connection indicator | refused placeholder | FAILURE | Connection refused | Sample parsing | `<evidence-path>` |
| Endpoint missing | endpoint evidence | `<endpoint-name-placeholder>` present | FAILURE | Missing evidence | Sample parsing | `<evidence-path>` |
| Endpoint intentionally disabled placeholder | disable record | explicit `<endpoint-name-placeholder>` record | REVIEW | Missing justification | Documentation review | `<evidence-path>` |
