# ZT-VIS-001 Centralized Telemetry and Security Event Correlation Foundation

## Purpose, scope, and status

ZT-VIS-001 centralizes selected sanitized validator and repository-validation
summaries into one local JSONL event model and applies deterministic correlation.
It is IMPLEMENTED and RUNTIME_VALIDATED, with bounded runtime validation
VALIDATED and acceptance ACCEPTED. Current maturity is UNASSESSED and the
bounded target is INITIAL.

The package maps conservatively to ZT-7.1, ZT-7.2, ZT-7.3, ZT-8.2, and ZT-8.6.
ZT-7.4 is excluded because no user/device behavior analysis exists.

## Current-state audit and architecture decision

The first execution established the repository-controlled local JSONL pipeline
over the existing restricted validators. The accepted persistent increment now
runs pinned Grafana, Loki, and Alloy containers on the dedicated monitoring VM.
Multiple competing stacks, Wazuh, and commercial SIEM products remain outside
this package.

~~~mermaid
flowchart LR
  O["OpenStack validator"] --> C["Local collector"]
  E["EVE validator"] --> C
  R["Router validator"] --> C
  G["Repository validator"] --> C
  C --> J["Approved sanitized runtime JSONL"]
  J --> A["Alloy"]
  A --> L["Persistent Loki"]
  L --> G["Loopback Grafana"]
~~~

## Event and correlation model

The event schema distinguishes event time from ingestion time, preserves source
type, uses normalized severity, permits null values, and never invents actor
identity. Sensitive dynamic identifiers are redacted before normalization.

~~~mermaid
flowchart LR
  S["Sanitized summaries"] --> N["Normalizer"]
  N --> V["Schema checks"]
  V --> J["JSONL events"]
  J --> C["Deterministic rules"]
  C --> F["Findings"]
~~~

Seven explainable rules cover authentication repetition, restricted-command
denial, validator failure/freshness, service health, network health, and
evidence-generation failure. Allowed actions are LOG, ALERT, CREATE_EVIDENCE,
and REQUIRE_REVIEW only. No rule blocks, terminates, isolates, or modifies
policy.

## Security, minimization, and retention

Collection invokes only existing forced-command endpoints with BatchMode.
There is no direct administrator credential, SSH restriction bypass, remote
host change, broad filesystem scan, Docker socket mount, or personal workstation
collection. Raw validator runtime is stored only under
.runtime/zero-trust/telemetry/ and is ignored. Only approved sanitized JSONL is
copied to the dedicated VM input directory. Loki retains it for 14 days;
Grafana and Loki data survive container restart. Reviewed summaries contain no
usernames, addresses, UUIDs, tokens, MAC addresses, or private paths.

Operational monitoring reports health and validator state. Security analytics
is limited to normalized, deterministic correlation. Neither is described as a
complete SIEM, UEBA system, production SOC, or continuous trust evaluator.

## Validation and evidence flow

~~~mermaid
flowchart LR
  L["Live collection"] --> S["Sanitization"]
  S --> N["164 normalized events"]
  N --> C["Live correlation"]
  T["Controlled fixture"] --> C
  C --> E["Reviewed package evidence"]
  E --> H["Human review boundary"]
~~~

Four running sources produced 164 normalized events with zero rejections.
Live correlation produced no finding, while the controlled validator-failure
fixture produced one expected finding. The package returned 8 PASS, 0 WARN,
0 FAIL, and exit code 0. The persistent increment then passed three service
health checks, three loopback endpoint checks, 336-hour retention, sanitized
event ingestion/query, secret-pattern scanning, and pre/post-restart retrieval
of the same event.

P1-VIS-CLOSE revalidated the current boundary on 2026-07-27. Four fixed source
transports produced 170 attributed sanitized events: 166 PASS and four retained
OpenStack diagnostic FAIL events. Those failures produced two live findings and
were not relabeled. Service health, runtime loopback listeners, retention,
ingestion, ownership and permissions, freshness, restart persistence, and
power-state rollback passed. KVM RTC alignment passed within the sequential
measurement bound; external NTP UDP/123 replies were unavailable, so persistent
NTP synchronization is not claimed.

## Limitations and remaining gaps

Persistent single-node storage and a loopback dashboard are implemented. Host
journal ingestion, full OpenStack log ingestion, external alert delivery,
behavior analytics, high availability, persistent NTP synchronization,
continuous operation, central visibility, and automated response remain absent.
Rollback is documented in
[zt-vis-001-rollback.md](zt-vis-001-rollback.md).
