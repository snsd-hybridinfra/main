# Bounded device-trust decision model

Status: `POLICY DESIGN`. No access-enforcement point consumes these decisions.

Inputs are inventory presence, owner role, management state, patch state,
vulnerability-assessment state, endpoint-agent state, compliance profile,
assessment freshness, approved identity association, and network zone.
Sensitive hardware fingerprints are not inputs.

| Decision | Deterministic condition |
|---|---|
| `TRUSTED_FOR_LAB_ACCESS` | Managed asset, current assessment, all mandatory controls pass, and no blocking finding. |
| `LIMITED_ACCESS` | Registered asset with current evidence and a non-blocking maintenance or scanner gap. |
| `REVIEW_REQUIRED` | Declared/partially managed asset, stale evidence, unknown owner, or exception pending. |
| `DENY_RECOMMENDED` | Unknown asset, blocking compliance failure, or revoked authorization association. |
| `UNKNOWN` | Required evidence cannot be obtained safely. |

The Phase 1 validator only recommends a decision. Real-time authorization,
network quarantine, account denial, and endpoint isolation are absent.
