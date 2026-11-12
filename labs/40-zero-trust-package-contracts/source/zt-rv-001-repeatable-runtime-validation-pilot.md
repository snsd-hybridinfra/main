# ZT-RV-001 Repeatable Runtime Validation Pilot

## Purpose and scope

This package implements one manual evidence-continuity campaign for
`ZT-4.1.1` 접근통제. The selected `ZTCV-VAL-SYS` validator runs only through
the fixed `ZT-CV-WF-001` read-only workflow at the unchanged seven-system lab
scope. `ZT-8.1`, `ZT-8.2`, `ZT-7.1`, and `ZT-3.1.1` were rejected for this
campaign because they are lower in the current overlay or blur EC4 with
automation or EC6 objectives.

The inherited capability evidence is EC3. The campaign requires three unique,
consecutive, sanitized successes at least 24 hours apart, with a stable plan,
validator version, target-scope fingerprint, and zero blocking failures. Five
known warning categories may remain visible. Duplicate IDs, evidence hashes,
or fingerprints never increase continuity.

## Campaign execution flow

```mermaid
flowchart LR
  A["Check campaign"] --> B["Generate fixed plan"]
  B --> C{"24-hour gate"}
  C -->|open| D["Execute read-only workflow"]
  C -->|closed| E["Stop without execution"]
  D --> F["Sanitize and verify"]
  F --> G["Write ignored candidate record"]
```

## Independence validation

```mermaid
flowchart TD
  A["Candidate"] --> B{"Unique ID, hashes, fingerprint"}
  B --> C{"Stable plan, validator, scope"}
  C --> D{"Security and sanitizer pass"}
  D --> E{"At least 24 hours"}
  E --> F["Eligible for explicit append review"]
```

The target fingerprint includes only safe architecture identifiers. Validator
tracking uses an explicit version plus the normalized file SHA-256. The
execution fingerprint includes campaign and plan identities, the sanitized
result hash, and timestamp; it is not a digital signature.

## History and assessment flow

```mermaid
flowchart LR
  A["Runtime candidate"] --> B["append tool check"]
  B --> C["Human diff review"]
  C --> D["Explicit append mode"]
  D --> E["Verification history"]
  E --> F["Proposal-only assessment"]
```

The live wrapper never appends history. The append tool may change only the
verification history and requires an explicit approval reference. Assessment
outputs stay under ignored runtime paths and never update baseline, acceptance,
gap, or maturity authorities automatically.

## EC3-to-EC4 boundary

```mermaid
flowchart LR
  R1["Accepted run 1: EC3"] --> R2["Accepted run 2: provisional"]
  R2 --> R3["Accepted run 3"]
  R3 --> G{"All consistency and separation gates"}
  G -->|pass| E["EC4 accepted after explicit review"]
  G -->|fail| H["Remain below EC4"]
```

The campaign completed three reviewed successes at
`2026-07-28T08:28:25.829099Z`, `2026-07-30T00:28:34.120022Z`, and
`2026-08-01T23:00:20.110724Z`. The accepted result is bounded EC4 for the
selected fixed campaign.

The separate ZT-SCH-001 task is installed and disabled, has zero accepted
scheduled dates, and is deferred to the final Phase 5 gate. The RV campaign's
own automatic schedule remains disabled. EC5, EC6, EC7,
maturity promotion, automatic retry, remediation, mutation, commit, and push
remain outside this package. The
historical first-run gate at `2026-07-23T04:57:52.159854Z` preserved separation
from the accepted CV baseline; later intervals also exceeded 24 hours.

## Freshness refresh progress

The historical three-run EC4 decision remains unchanged. Under the temporary
`P1-RV-FRESHNESS-001` exception, a new manual freshness window is tracked
separately in `recovery/P1-ACC-001/rv-refresh-progress.yaml`.

The first refreshed execution, `ZTRV-20260820T115907Z-fd3d6d3c`, completed at
`2026-08-20T11:59:07.686986Z` with 4 PASS / 6 WARN / 0 FAIL, sanitization PASS,
and 9/9 negative security-boundary checks blocked. It was explicitly reviewed
and appended. The refresh remains 1/3 at EC3 and cannot close the stale finding;
the second execution is not eligible before `2026-08-21T11:59:07.686986Z`.
No scheduler, automatic retry, target mutation, or package promotion was used.
