# ADR 0020: Persistent AI Agent Sandbox as the Flagship PaaS Blueprint

- Status: Accepted for local design and contract validation
- Date: 2026-08-27
- Decision owner: Financial Hybrid-Ready IDP architecture
- Runtime status: `PARTIALLY_IMPLEMENTED_LOCAL / NOT_VALIDATED`

## Context

Long-running AI engineering work must survive a closed browser or sleeping developer workstation, execute untrusted repository code away from the developer endpoint, and expose queue, startup, inference, tool, test and cleanup latency. The user-provided industry brief is design input only; it is not an independently verified repository authority.

The existing catalog already contains eight approved composite blueprints. A separate ninth product would duplicate the bounded runner concept and weaken the fixed catalog boundary.

## Decision

Replace `CI_CD_RUNNER` with `AI_AGENT_SANDBOX`. The new blueprint subsumes bounded CI/CD execution and composes only `K3S_RUNTIME`, `OBJECT_STORAGE`, `NETWORK_POLICY` and `OPERATIONS_PROFILE`. Users still choose only blueprint, environment, size, duration and purpose. Repository, Git authorization and model access are supplied through separately governed service integrations, not free-form catalog inputs.

Persistence belongs to the control plane, not to a long-lived pod. Durable job state, policy decisions, checkpoints and artifact references survive; disposable execution pods may be deleted and recreated. Approval waiting checkpoints the job, deletes compute and resumes in a new pod after an explicit decision.

Untrusted code requires a sandboxed Kubernetes `RuntimeClass` such as Kata Containers or gVisor. A plain default container runtime is not accepted as the isolation boundary. Pods are non-root, capability-free, seccomp-confined, read-only except for bounded workspace and scratch volumes, denied host namespaces and mounts, and have no automatic service-account token.

Outbound traffic is default-deny and passes through an authenticated, FQDN-aware egress broker. Kubernetes NetworkPolicy alone is not evidence of domain-only enforcement. Direct IP, alternate DNS, tunnel and unapproved package-source bypasses must be denied. GitHub App and model-broker credentials are short-lived and task-scoped; developer SSH keys, browser sessions and raw model-provider keys never enter the sandbox.

The orchestrator enforces hard limits for wall time, iterations, model tokens, monetary cost, external calls, concurrency and egress bytes. Request-count rate limiting alone is insufficient. Direct pushes to `main` are prohibited. Work is written to an ephemeral task branch as atomic checkpoints and offered through a Draft pull request after diff, secret and policy checks.

## Human approval

Workspace edits and allow-listed build or test commands may be pre-authorized per task. Main-branch mutation, branch-protection bypass, production access, schema migration, secret access, new egress, infrastructure mutation and dependency-source changes require a recorded asynchronous decision. A waiting job is `AWAITING_APPROVAL`; it is not represented by an indefinitely suspended pod.

## Consequences

- The product catalog remains exactly eight blueprints.
- `VM_APPLICATION_STACK` remains the only locally executable composite path.
- `AI_AGENT_SANDBOX` resolves fail-closed because object storage, the authenticated egress broker, runtime credentials, the approved image and the target cluster are not connected. Locally validated Redis Streams and Kubernetes client adapters do not remove these external gates.
- This decision creates no live cluster, model, GitHub, queue, Istio, storage or observability resource and grants no runtime credit.
- Platform delivery status and Zero Trust package status remain independent; no new Zero Trust package ID or status promotion is created.

## Acceptance boundary

Implementation may be promoted only after positive execution, denied egress, bypass, checkpoint/resume, rollback/cleanup, runaway-budget termination, approval, token-expiry and sandbox-isolation checks produce reviewed sanitized evidence. Production repositories and data remain excluded.

The first local implementation slice persists job state in the request-service
database, emits a non-deployable digest-bound Job/NetworkPolicy/ResourceQuota
bundle, and validates checkpoint, approval, resume, completion, timeout and
rejection transitions through service-only simulation endpoints. It does not
clone a repository, call a model, create a pod, push Git, or provide runtime
evidence.

The second local slice adds a database outbox whose envelope is fixed to a
future Redis Streams `XADD`/`XREADGROUP` transport contract. It creates only
non-secret, locally invalid GitHub App and model-broker lease references, revokes
them on checkpoint or terminal transitions, and rotates them after approval or
resume. Egress decisions allow only an exact destination class, protocol and
port through an authenticated broker. No Redis connection, credential token,
DNS request or external network call is made.

The third local slice adds an optimistic, idempotent pre-execution budget
reservation ledger for wall time, iterations, model tokens, monetary cost,
external calls, concurrency and egress bytes. A denied reservation moves the
job to `BUDGET_EXHAUSTED`, cancels its queue item, releases compute and revokes
active leases atomically. A fixed-schema trace-event store accepts only known
span names, identifiers, outcomes and numeric measurements; it has no field for
prompt, source, arbitrary attributes or secret data. No OpenTelemetry exporter
or external meter is connected.

The fourth local slice adds injectable Redis Streams publish, consumer-group
claim and acknowledgement operations plus an ordered Kubernetes controller for
Namespace, ResourceQuota, NetworkPolicy and Job creation. Activation requires
matching source and approval digests, an unexpired decision, the `kata-qemu-runtime-rs`
RuntimeClass and an approved digest-pinned internal image. Partial creation
rolls back only the newly created task namespace. These adapters pass local
fake-client positive, negative and rollback tests; no Redis endpoint,
Kubernetes context, image, credential, broker or live resource is present.
