# ZT-AUTO-001 Policy Automation Foundation

## Purpose and accepted scope

ZT-AUTO-001 implements a bounded single-workstation orchestration foundation
for existing repository validators. It registers fixed handlers, evaluates a
default-deny policy, produces an immutable deterministic plan, runs only R0 to
R3 read-only or local-artifact actions, sanitizes evidence, and records every
outcome. It is not a general command runner, remote shell, SOAR platform, or
autonomous response system.

The accepted live result is one `EXECUTE_READ_ONLY` cross-domain workflow with
plan hash `c64b56bfdb0831b91290f051ea385e4c7fefbe53afe665ac340e2545accaba32`.
It returned `PARTIAL`, 4 PASS, 4 WARN, 0 FAIL, and exit code 0. The warnings
retain the accepted predecessor states rather than hiding them.

## Capability boundary

All six canonical automation-integration capabilities come from 제로트러스트
가이드라인 2.0, printed pages 87-89, Table 3-39. ZT-8.1 정책 통합 and
ZT-8.2 중요 프로세스 자동화 receive bounded implementation and partial runtime
evidence. ZT-8.5 데이터 교환 표준화 and ZT-8.6 보안 운영 조정 및 사고 대응 are
reference-only contributions. ZT-8.3 인공지능 and ZT-8.4 보안 통합, 자동화 및
대응 remain gaps. Every source maturity characteristic remains
`SOURCE_DEFINED_NOT_ASSESSED`; package target `INITIAL` is a plan, not a current
maturity assignment.

## Current automation landscape

The inventory records repository, OpenStack, EVE-NG, router, endpoint, system,
telemetry, correlation, policy, workflow, and review-handoff integrations.
Existing fixed local and restricted live validators are reusable. Persistent
Grafana/Loki/Alloy telemetry is live for approved sanitized JSONL. Email,
Slack, webhook, ticketing, GitHub issue, and incident-management delivery are
absent, so notifications and incident handoffs remain local proposals. There
is no suitable existing GitHub Actions validation workflow; this package adds
no CI workflow and no live credential dependency.

## Selected orchestration model

```mermaid
flowchart LR
  A["Sanitized telemetry or operator request"] --> B["Default-deny policy evaluation"]
  B --> C["Deterministic workflow plan"]
  C --> D{"Risk and approval gate"}
  D -->|"R0-R3 allowed"| E["Fixed handler"]
  D -->|"R4-R8"| F["Blocked or proposal only"]
  E --> G["Sanitized evidence"]
  G --> H["Human review"]
```

Actions name a reviewed handler ID; YAML cannot supply an executable, remote
target, command, working directory, or command fragment. The Python runner
resolves the handler in code, uses argument arrays with `shell=False`, an
explicit environment allowlist, fixed timeouts, no interactive prompt, and a
repository-root working directory. Positive parameter allowlists reject path
traversal, shell metacharacters, unapproved hosts, aliases, and paths.

## Action, workflow, risk, and approval registries

Thirteen actions cover repository validation, taxonomy sync, system inventory,
configuration drift, service state, restricted live system validation,
telemetry validation, evidence summary, and local governance/review proposals.
Six workflows cover cross-domain validation, evidence handling, deterministic
correlation review, drift review, gap proposal, and incident-review handoff.

R0 is read-only, R1 is local runtime-artifact write, R2 is repository-status
proposal, and R3 is approved remote read-only validation. R4 through R7 are
future change categories requiring stronger approval and cannot execute here;
R8 is prohibited. Committed policy is not human approval. The live R3 path is
allowed only because it reuses previously accepted fixed package policies and
destinations. Proposal-only actions require operator review and never update
authoritative files.

```mermaid
flowchart TD
  A["Catalog validation"] --> B["Policy decision"]
  B -->|"deny"| X["Blocked audit record"]
  B -->|"allow"| C["Canonical plan"]
  C --> D["SHA-256 plan hash"]
  D --> E{"Approval requirement satisfied?"}
  E -->|"no"| Y["Blocked by approval"]
  E -->|"yes"| F["Immutable execution input"]
```

## Restricted execution and evidence

Check and plan modes perform no action. Execute-read-only invokes only fixed
handlers. Proposal-only writes solely under the ignored automation runtime.
Each workflow has one local lock with owner metadata; duplicates are rejected,
stale locks are reported and never silently removed. Actions are bounded by
timeouts. Retry defaults to `NONE`; no approval, policy, schema,
authentication, secret-scan, or change failure is retried.

```mermaid
sequenceDiagram
  participant O as Orchestrator
  participant H as Fixed handler
  participant R as Ignored runtime
  participant E as Sanitized evidence
  O->>H: Argument array, fixed target, timeout
  H-->>O: Exit code and bounded output
  O->>R: Raw execution record and sanitized step files
  O->>E: Reviewed aggregate only
  E-->>O: Schema and secret-boundary result
```

Child exit codes propagate; mandatory failure is never converted to a warning.
`PASS`, `WARN`, `FAIL`, `SKIPPED`, unavailable, blocked, timed-out, and execution
error states remain distinct. Runtime data, locks, plans, proposals, and raw
execution records remain ignored. The committed evidence is a manually
reviewed aggregate with paths and sensitive values removed.

## Failure, rollback, and human review

Read-only actions need no infrastructure rollback. Generated runtime artifacts
may be removed or restored only through an explicit cleanup decision; failed
workflow evidence is retained as incomplete rather than silently deleted.
Future mutation actions define reference boundaries only and have no handler.

```mermaid
flowchart TD
  A["Action result"] --> B{"PASS or WARN?"}
  B -->|"yes"| C["Continue by declared condition"]
  B -->|"no"| D["Stop dependent mandatory steps"]
  D --> E["Retain incomplete evidence"]
  E --> F{"Artifact-only compensation?"}
  F -->|"reviewed"| G["Delete or restore generated artifact"]
  F -->|"not reviewed"| H["Preserve for human review"]
  C --> I["Proposal or summary"]
  I --> H
```

Correlation findings may produce evidence, a plan, a change proposal, or a
review package. They cannot block traffic, isolate an account or workload,
restart a service, modify a firewall or route, rotate a credential, or declare
a confirmed incident. No authoritative baseline, gap, risk, or implementation
record is automatically rewritten.

## Status and remaining gaps

The package is `IMPLEMENTED / PARTIALLY_RUNTIME_VALIDATED`, with current
maturity `UNASSESSED`. It has one partial live cycle, not repeatable or
scheduled evidence. A warning-free integrated run, reviewed external
notification and incident-management channels, time-separated repeatability,
and capability-specific maturity assessment remain open. ZT-CV-001 is the next
package; ZT-RV-001 and ZT-SCH-001 remain later gated work.
