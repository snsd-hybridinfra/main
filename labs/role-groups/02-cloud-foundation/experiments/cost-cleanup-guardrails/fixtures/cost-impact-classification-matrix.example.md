# Cost Impact Classification Matrix

| Resource Category | Cost Signal | Risk Level | Required Evidence | Cleanup Mapping | Related Scenario | Final Judgment |
|---|---|---|---|---|---|---|
| Compute instance placeholder | monthly estimate | Medium | owner | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Persistent volume placeholder | retained capacity | Medium | owner/retention | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Public IP placeholder | allocated address | Medium | owner/exposure review | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Load balancer placeholder | hourly estimate | Medium | owner | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Object storage placeholder | growth/retention | Medium | owner/retention | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| NAT gateway placeholder | usage estimate | High | owner/approval | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Managed database placeholder | capacity estimate | High | owner/retention | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Kubernetes node placeholder | node count | Medium | owner | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Monitoring storage placeholder | retention growth | Medium | owner/retention | retired-numbered-case | retired-numbered-case/retired-numbered-case | COST_REVIEW_REQUIRED |
| Orphaned resource placeholder | cost without owner | High | cleanup evidence | retired-numbered-case required | retired-numbered-case | COST_GUARDRAIL_FAIL |

Critical spikes require approval. Missing estimates are `COST_EVIDENCE_INCOMPLETE`.
