# Security Rule Rollback Decision Matrix

| Detected Rule | Exposure Level | Business Justification | Temporary Exception Allowed | Required Approval Placeholder | Rollback Action | Validation Evidence | Final Judgment |
|---|---|---|---|---|---|---|---|
| Critical public admin exposure | Critical | none-placeholder | No | `<security-approval-placeholder>` | restrict to bastion | post rules | ROLLBACK_REQUIRED |
| Critical public DB exposure | Critical | none-placeholder | No | `<security-approval-placeholder>` | restrict to application subnet | post rules | ROLLBACK_REQUIRED |
| Public internal API exposure | High | none-placeholder | No | `<service-owner-approval-placeholder>` | remove public access | post rules | ROLLBACK_REQUIRED |
| Temporary maintenance exception | Medium | `<reason-placeholder>` | Conditional | `<change-approval-placeholder>` | remove at expiry | rollback evidence | REVIEW |
| Approved bastion-only SSH | Low | administration-placeholder | Yes | `<owner-approval-placeholder>` | retain/review | pre rules | SAFE |
| Approved service-to-service access | Low | application-placeholder | Yes | `<owner-approval-placeholder>` | retain/review | pre rules | SAFE |
| Missing owner | High | unknown | No | `<owner-placeholder>` | block/rollback | metadata | INCOMPLETE |
| Missing expiry | High | unknown | No | `<expiry-approval-placeholder>` | block/rollback | metadata | INCOMPLETE |
| Missing rollback evidence | High | unknown | No | `<reviewer-placeholder>` | collect/rollback | validation | INCOMPLETE |
