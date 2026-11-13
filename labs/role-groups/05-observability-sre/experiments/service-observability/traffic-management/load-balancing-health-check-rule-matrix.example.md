# Load Balancing Health Check Rule Matrix Example

NON-PRODUCTION EXAMPLE. All targets and settings are symbolic.

| Health Check Control | Required Setting | Approved Placeholder Value | Purpose | Failure Condition | Validation Method | Evidence Reference |
|---|---|---|---|---|---|---|
| backend pool definition | upstream pool | `<backend-pool>` | Group candidate backends | Pool or members missing | Static config review | `<evidence-path>` |
| backend health path | health route | `<backend-health-path>` | Define health observation path | Path missing | Config/document review | `<evidence-path>` |
| expected HTTP status code | healthy response | `<expected-status-code>` | Define healthy judgment | Status not acceptable | Sample parsing | `<evidence-path>` |
| health check interval | observation interval | `<health-check-interval>` | Bound observation frequency | Interval missing | Documentation review | `<evidence-path>` |
| timeout | request timeout | `<health-check-timeout>` | Bound health request duration | Timeout missing | Config/document review | `<evidence-path>` |
| retry / unhealthy threshold | retry and failure count | `<unhealthy-threshold>` | Define review threshold | Threshold missing | Config/document review | `<evidence-path>` |
| healthy backend count | backend evidence count | `<healthy-backend-count>` | Confirm pool availability | No healthy backend | Sample parsing | `<evidence-path>` |
| unhealthy backend detection | failed status/timeout detection | `<unhealthy-threshold>` | Detect degraded members | Failure not classified | Sample parsing | `<evidence-path>` |
| backend exclusion behavior | manual mark-unhealthy/exclusion | `<backend-exclusion-decision>` | Prevent unsafe routing | Failed backend remains approved | Documentation review | `<evidence-path>` |
| manual recovery / failover reference | operator runbook reference | `<manual-recovery-reference>` | Govern recovery and re-admission | Automatic failover claimed | Documentation review | `<evidence-path>` |
