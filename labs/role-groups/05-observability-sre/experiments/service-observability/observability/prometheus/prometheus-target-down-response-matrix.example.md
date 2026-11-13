# Prometheus Target Down Response Matrix

| Signal | Example Evidence | Meaning | Immediate Check | Recovery / Rollback Action | Validation Owner Scenario |
|---|---|---|---|---|---|
| target health up | health up | scrape healthy | up value | none | retired-numbered-case |
| target health down | health down | scrape failed | last error | inspect exporter | retired-numbered-case |
| up = 1 | query value 1 | target reachable | target state | none | retired-numbered-case |
| up = 0 | query value 0 | target unavailable | exporter/path | manual recovery | retired-numbered-case |
| scrape error | placeholder | scrape failed | error category | investigate | retired-numbered-case |
| context deadline exceeded | placeholder | timeout | network/exporter | investigate | retired-numbered-case |
| connection refused | placeholder | listener unavailable | service state | manual start | retired-numbered-case |
| no route to host placeholder | placeholder | path unavailable | routing | separate runbook | retired-numbered-case |
| alert firing | firing | sustained target down | target/up | recover | retired-numbered-case |
| alert resolved | inactive | condition cleared | target/up | close | retired-numbered-case |
| post-recovery target up | up/value 1 | recovered | timing | complete | retired-numbered-case |
