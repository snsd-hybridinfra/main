# Load Balancer Failure Response Matrix

| Signal | Example Evidence | Meaning | Immediate Check | Recovery / Rollback Action | Validation Owner Scenario |
|---|---|---|---|---|---|
| LB 200 | healthy placeholder | entrypoint healthy | compare backends | none | retired-numbered-case |
| LB 503 | unavailable placeholder | entrypoint unhealthy | direct backend health | manual recovery | retired-numbered-case |
| timeout/refused | failure placeholder | LB path unavailable | service state | manual recovery | retired-numbered-case |
| backends 200 while LB down | isolated placeholder | backend layer healthy | LB configuration/service | restore LB | retired-numbered-case |
| client restored | 200 placeholder | path recovered | rollback bypass | normal path | retired-numbered-case |
