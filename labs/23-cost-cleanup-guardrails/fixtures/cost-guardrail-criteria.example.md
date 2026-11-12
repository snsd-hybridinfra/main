# Cost Guardrail Criteria

| Guardrail Area | Evaluation Input | Expected Condition | Violation Condition | Severity | Exception Requirement | Related Scenario | Evidence Reference |
|---|---|---|---|---|---|---|---|
| Monthly budget threshold | estimate | within placeholder | exceeded | High | Full fields | retired-numbered-case | `<evidence-path>` |
| Daily budget threshold | estimate | within placeholder | exceeded | High | Full fields | retired-numbered-case | `<evidence-path>` |
| Incremental cost delta | delta | within placeholder | exceeded | High | Full fields | retired-numbered-case | `<evidence-path>` |
| Cost-impacting Terraform change | plan metadata | retired-numbered-case mapped | missing | Medium | Review | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Drift remediation cost impact | retired-numbered-case evidence | cost review | missing | High | Approval | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Public IP cost exposure | classification | owner/exposure review | missing | Medium | Full fields | retired-numbered-case | `<evidence-path>` |
| Persistent volume cost exposure | classification | owner/retention | missing | Medium | Full fields | retired-numbered-case | `<evidence-path>` |
| Object storage retention | classification | retention/cleanup | missing | Medium | Full fields | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Oversized compute placeholder | estimate | reviewed | unreviewed | Medium | Approval | retired-numbered-case | `<evidence-path>` |
| Orphaned resource cleanup mapping | mapping | retired-numbered-case | absent | High | Not allowed | retired-numbered-case | `<evidence-path>` |
| Missing owner | exception | present | absent | High | Reject | retired-numbered-case | `<evidence-path>` |
| Missing expiry | exception | present | absent | High | Reject | retired-numbered-case | `<evidence-path>` |
| Missing approval | exception | present | absent | Critical | Reject | retired-numbered-case | `<evidence-path>` |
| Missing retired-numbered-case cleanup mapping | cleanup | present | absent | High | Review | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
