# Resource Cleanup Criteria

| Cleanup Area | Candidate Evidence | Expected Condition | Cleanup Condition | Block Condition | Required Approval | Related Scenario | Evidence Reference |
|---|---|---|---|---|---|---|---|
| Orphaned compute resource | inventory | owner absent/idle | review | dependency | Required | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Stopped compute resource placeholder | inventory | lifecycle reviewed | expired | active owner | Required | retired-numbered-case | `<evidence-path>` |
| Unattached volume | inventory | retention reviewed | orphaned | backup dependency | Required | retired-numbered-case | `<evidence-path>` |
| Unused public IP | inventory | exposure/cost reviewed | unused | dependency | Required | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Unused load balancer | inventory | traffic dependency reviewed | unused | active traffic | Required | retired-numbered-case | `<evidence-path>` |
| Empty object storage bucket | inventory | retention reviewed | empty/expired | retention | Required | retired-numbered-case | `<evidence-path>` |
| Expired temporary resource | lifecycle | expired | cleanup ready | exception | Required | retired-numbered-case | `<evidence-path>` |
| Missing owner | metadata | owner present | review | missing | Required | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Missing retention class | metadata | present | review | missing | Required | retired-numbered-case | `<evidence-path>` |
| Missing cost classification | retired-numbered-case | present | review | missing | Required | retired-numbered-case | `<evidence-path>` |
| Active exception | exception | honored | not cleanup | active | Required | retired-numbered-case | `<evidence-path>` |
| Critical dependency risk | impact | low | none | critical | Required | retired-numbered-case | `<evidence-path>` |
| Missing rollback evidence | plan | present | none | missing | Required | retired-numbered-case/retired-numbered-case | `<evidence-path>` |
| Missing retired-numbered-case cost mapping | mapping | present | none | missing | Required | retired-numbered-case | `<evidence-path>` |
| Missing retired-numbered-case final report mapping | mapping | present | none | missing | Required | retired-numbered-case | `<evidence-path>` |

Drift detection maps retired-numbered-case, remediation retired-numbered-case, Policy as Code retired-numbered-case, cost retired-numbered-case, and reporting retired-numbered-case.
