# Cost Guardrail Decision Matrix

| Evaluation Result | Example Evidence | Operational Meaning | Required Action | Exception Handling | Final Judgment |
|---|---|---|---|---|---|
| Cost within threshold | pass sample | Acceptable | Record | None | COST_GUARDRAIL_PASS |
| Monthly threshold exceeded | fail sample | Budget risk | Review | Full fields | COST_GUARDRAIL_FAIL |
| Daily threshold exceeded | fail sample | Spend-rate risk | Review | Full fields | COST_GUARDRAIL_FAIL |
| Incremental cost delta exceeded | fail sample | Change risk | Review | Full fields | COST_GUARDRAIL_FAIL |
| Critical cost spike placeholder | spike sample | Critical | Stop | Approval | COST_REVIEW_REQUIRED |
| Approved temporary exception | exception | Temporary | Track | Complete | COST_EXCEPTION_APPROVED |
| Missing estimate | incomplete | Cannot judge | Collect | None | COST_EVIDENCE_INCOMPLETE |
| Missing owner | incomplete | No accountability | Reject | Reject | COST_REVIEW_REQUIRED |
| Missing expiry | incomplete | Unbounded | Reject | Reject | COST_REVIEW_REQUIRED |
| Missing approval | incomplete | Unauthorized | Reject | Reject | COST_GUARDRAIL_FAIL |
| Missing cleanup mapping | incomplete | Orphan risk | Map retired-numbered-case | None | COST_REVIEW_REQUIRED |
| Cost input malformed | parse failure | Cannot judge | Correct | None | COST_EVIDENCE_INCOMPLETE |
