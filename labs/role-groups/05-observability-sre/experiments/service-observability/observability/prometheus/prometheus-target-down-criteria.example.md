# Prometheus Target Down Criteria

| Validation Phase | Evidence Source | Expected Condition | Failure Condition | Operational Judgment | Related Scenario | Evidence Reference |
|---|---|---|---|---|---|---|
| Pre-failure target discovery | targets | target exists | missing | baseline | retired-numbered-case | pre targets |
| Pre-failure target UP state | targets/up | health up and value 1 | down/0 | baseline | retired-numbered-case | pre samples |
| Manual target-down injection | event | manual stop marker | automated | controlled | retired-numbered-case | injection |
| Prometheus target DOWN detection | targets | health down | not detected | detected | retired-numbered-case | down targets |
| up metric equals 0 | query | value 0 | value 1 | detected | retired-numbered-case | down query |
| Alert rule evaluation placeholder | rule | placeholder defined | missing | governed | retired-numbered-case | alert example |
| Alert firing placeholder | alerts | firing | absent | alerted | retired-numbered-case | down alerts |
| Recovery action placeholder | event | manual start marker | automated | recovering | retired-numbered-case | recovery |
| Post-recovery target UP state | targets/up | health up/value 1 | down/0 | recovered | retired-numbered-case | post samples |
| Alert cleared placeholder | alerts | inactive/resolved | firing | recovered | retired-numbered-case | cleared alerts |
| Recovery time threshold | timing | within threshold | exceeded/missing | review | retired-numbered-case | summary |
