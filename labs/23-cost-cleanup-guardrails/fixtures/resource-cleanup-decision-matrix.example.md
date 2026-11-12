# Resource Cleanup Decision Matrix

| Evaluation Result | Example Evidence | Operational Meaning | Required Action | Exception Handling | Final Judgment |
|---|---|---|---|---|---|
| Cleanup not required | active use | Retain | Record | None | CLEANUP_NOT_REQUIRED |
| Cleanup ready | complete candidate | Eligible | Manual review | None | CLEANUP_READY |
| Cleanup blocked by active owner | owner active | Retain | Confirm | None | CLEANUP_BLOCKED |
| Cleanup blocked by retention policy | retention active | Retain | Wait | Exception | CLEANUP_BLOCKED |
| Cleanup blocked by dependency risk | critical dependency | Unsafe | Stop | None | CLEANUP_BLOCKED |
| Cleanup blocked by missing rollback evidence | no rollback | Unsafe | Add note | None | CLEANUP_BLOCKED |
| Cleanup blocked by missing approval | no approval | Unauthorized | Reject | None | CLEANUP_BLOCKED |
| Approved temporary exception | complete exception | Retain temporarily | Track expiry | Complete | CLEANUP_EXCEPTION_APPROVED |
| Missing owner | incomplete | Review | Identify | None | CLEANUP_REVIEW_REQUIRED |
| Missing retention class | incomplete | Review | Classify | None | CLEANUP_REVIEW_REQUIRED |
| Missing cost mapping | incomplete | Cannot judge | Map retired-numbered-case | None | CLEANUP_EVIDENCE_INCOMPLETE |
| Candidate evidence malformed | parse failure | Cannot judge | Correct | None | CLEANUP_EVIDENCE_INCOMPLETE |
