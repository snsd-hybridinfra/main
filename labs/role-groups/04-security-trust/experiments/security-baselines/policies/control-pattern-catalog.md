# Zero Trust Control-Pattern Catalog

Control patterns are reusable architecture and validation patterns. They are not scenarios, product installation guides, or evidence of implementation. Technologies named below are **CANDIDATE ONLY** unless a current repository evidence reference explicitly proves otherwise.

## ZTP-ID-001 — Context-bound identity access

- **Addressed capabilities:** ZT-1.1.1, ZT-1.1.2, ZT-1.2.1, ZT-1.2.2, ZT-1.4.1, ZT-1.4.2
- **Purpose:** authenticate a known laboratory identity and authorize the minimum resource scope using current context.
- **Trust assumption removed:** network location alone establishes user trust.
- **Policy input:** identity, role, credential/MFA state, session age, device state, requested resource.
- **Policy decision concept:** permit, step-up, restrict, or deny according to explicit policy.
- **Enforcement point:** identity proxy, host access control, cloud IAM, or application authorization boundary.
- **Telemetry:** authentication, decision, session, denial, and privilege-use events.
- **Expected control action:** minimum-duration, minimum-scope access; invalid or stale context is denied or challenged.
- **Failure behavior:** deny privileged access; preserve a break-glass path subject to separate approval and evidence.
- **Rollback:** revoke test sessions/credentials and restore the last approved policy.
- **Validation method:** configuration check, positive/negative access test, stale-session test, and recovery test.
- **Evidence:** sanitized identities/roles, decision logs, deny/allow results, and rollback confirmation.
- **Limitations:** no enterprise lifecycle, biometric context, or organization-wide federation claim.
- **Candidate implementation technologies:** CANDIDATE ONLY — standards-based OIDC/SAML identity provider, MFA, SSH certificates, application RBAC.
- **Repository implementation status:** PLANNED.

## ZTP-DEV-001 — Device inventory and posture assertion

- **Addressed capabilities:** ZT-2.1.1, ZT-2.2.1, ZT-2.3.1, ZT-2.4.2
- **Purpose:** bind access decisions to a known host record and bounded compliance evidence.
- **Trust assumption removed:** any device presenting valid credentials is healthy.
- **Policy input:** asset identity, operating-system/version, patch/configuration state, owner, last-seen time.
- **Policy decision concept:** allow, restrict, quarantine-equivalent, or deny when required posture is missing.
- **Enforcement point:** administrative access, workload gateway, host firewall, or policy proxy.
- **Telemetry:** inventory changes, posture failures, authorization decisions, remediation results.
- **Expected control action:** unknown or non-compliant assets receive reduced or denied access.
- **Failure behavior:** mark posture unknown and prevent privileged access rather than inferring compliance.
- **Rollback:** restore prior approved configuration or remove the test device record.
- **Validation method:** inventory reconciliation, configuration check, expired posture test, and recovery test.
- **Evidence:** sanitized inventory, posture result, access decision, remediation and cleanup record.
- **Limitations:** no enterprise UEM/MDM or EDR/XDR coverage.
- **Candidate implementation technologies:** CANDIDATE ONLY — OS-native inventory, configuration-management facts, signed posture assertion.
- **Repository implementation status:** PLANNED.

## ZTP-NET-001 — Segmented flow with explicit enforcement

- **Addressed capabilities:** ZT-3.1.1, ZT-3.1.2, ZT-3.1.3, ZT-3.3.1, ZT-3.4.1, ZT-3.5.1, ZT-4.3.1
- **Purpose:** restrict inter-zone and workload flows to documented source, destination, service, and direction.
- **Trust assumption removed:** internal adjacency implies unrestricted reachability.
- **Policy input:** asset/workload identity, zone, flow map, service port, direction, exception metadata.
- **Policy decision concept:** allow only approved flows; deny or isolate all other tested paths.
- **Enforcement point:** router ACL, cloud security rule, workload/network policy, reverse proxy, or host firewall.
- **Telemetry:** flow counters, allow/deny results, routing state, policy changes.
- **Expected control action:** approved traffic succeeds and prohibited traffic fails without breaking required paths.
- **Failure behavior:** prefer bounded deny for protected assets; use tested failover/recovery for availability-sensitive services.
- **Rollback:** remove temporary rule and restore known-good policy/configuration.
- **Validation method:** positive, directional negative, bypass, policy-failure, and recovery tests.
- **Evidence:** sanitized topology/configuration, routing/flow state, deny/allow observations, rollback proof.
- **Limitations:** current evidence covers only the EVE-NG/OpenStack network foundation, not adaptive enterprise micro-segmentation.
- **Candidate implementation technologies:** CURRENT (bounded) — EVE-NG VLAN/routing/ACL and OpenStack networking evidence; CANDIDATE ONLY — workload policies and additional provider-native controls.
- **Repository implementation status:** PARTIALLY_VALIDATED.

## ZTP-SYS-001 — Restricted administration and credential boundary

- **Addressed capabilities:** ZT-4.1.1, ZT-4.2.1, ZT-4.2.2, ZT-4.4.1, ZT-5.3.1
- **Purpose:** expose administrative functions only through approved identities, paths, credentials, and environments.
- **Trust assumption removed:** possession of a static administrator secret is sufficient.
- **Policy input:** identity/role, credential type, source path, environment, requested privilege, change reference.
- **Policy decision concept:** grant time- and scope-bounded privilege or deny.
- **Enforcement point:** bastion, SSH/service access control, sudo/role boundary, cloud IAM.
- **Telemetry:** login, privilege escalation, credential lifecycle, policy decision, session end.
- **Expected control action:** direct or password-based paths are denied when not explicitly approved.
- **Failure behavior:** deny new privilege; documented recovery access must be independently controlled.
- **Rollback:** revoke temporary access, rotate affected test credential, restore policy.
- **Validation method:** configuration review, positive/negative login, direct-path bypass, failure and recovery tests.
- **Evidence:** redacted account/role configuration, access results, approvals, revocation evidence.
- **Limitations:** no production PAM vault or enterprise break-glass operations.
- **Candidate implementation technologies:** CANDIDATE ONLY — SSH certificates/keys, OS role controls, standards-based identity proxy, cloud-native IAM.
- **Repository implementation status:** PLANNED.

## ZTP-APP-001 — Authorized and verified workload delivery

- **Addressed capabilities:** ZT-5.1.1, ZT-5.2.1, ZT-5.4.1, ZT-5.4.2, ZT-5.5.1, ZT-5.5.2
- **Purpose:** admit only inventoried, authorized, policy-compliant application artifacts and continuously observe their bounded runtime state.
- **Trust assumption removed:** a deployable artifact is inherently trusted.
- **Policy input:** application identity, artifact digest/provenance, vulnerability result, configuration, environment, authorization context.
- **Policy decision concept:** admit, restrict, require review, or reject.
- **Enforcement point:** delivery gate, workload admission boundary, deployment controller, application authorization layer.
- **Telemetry:** build/deploy result, artifact metadata, policy decision, runtime health, drift.
- **Expected control action:** unknown, tampered, high-risk, or unauthorized artifacts are rejected.
- **Failure behavior:** stop promotion and retain last accepted workload; do not auto-remediate without approval.
- **Rollback:** redeploy the last approved artifact/configuration and verify service health.
- **Validation method:** static review, tampered-artifact negative test, policy test, failure injection, and recovery.
- **Evidence:** inventory, digest/provenance, scan/policy output, deployment/denial result, rollback health.
- **Limitations:** no production supply-chain attestation or organization-wide SDLC claim.
- **Candidate implementation technologies:** CANDIDATE ONLY — OCI registry metadata, SBOM format, image/dependency scanner, admission policy.
- **Repository implementation status:** PLANNED.

## ZTP-DATA-001 — Classified data access and protection

- **Addressed capabilities:** ZT-6.1.1, ZT-6.2.1, ZT-6.3.1, ZT-6.4.1, ZT-6.5.2
- **Purpose:** inventory and label approved test data, then enforce identity- and classification-aware access and protection.
- **Trust assumption removed:** authenticated workload access permits all data operations.
- **Policy input:** data asset/classification, identity/role, workload, purpose, environment, encryption/key state.
- **Policy decision concept:** permit minimum operation, mask/restrict, or deny.
- **Enforcement point:** database/application authorization, storage permission, encryption boundary.
- **Telemetry:** access decision, query/operation class, label/key changes, backup/restore result.
- **Expected control action:** unlabeled or unauthorized access is denied; approved access is auditable.
- **Failure behavior:** fail closed for protected data; preserve recoverability and test-data integrity.
- **Rollback:** restore label/policy/key reference or recover approved test data from backup.
- **Validation method:** configuration check, allowed/denied access, missing-label/key test, backup/recovery test.
- **Evidence:** synthetic data inventory, labels, redacted decisions, protection configuration, recovery proof.
- **Limitations:** only synthetic laboratory data; no enterprise data governance or DLP claim.
- **Candidate implementation technologies:** CANDIDATE ONLY — database roles, application authorization, OS/storage encryption, test key-management pattern.
- **Repository implementation status:** PLANNED.

## ZTP-VA-001 — Normalized telemetry and bounded correlation

- **Addressed capabilities:** ZT-7.1, ZT-7.3, ZT-7.4
- **Purpose:** collect relevant lab signals using a consistent schema and correlate only supported operational/security conditions.
- **Trust assumption removed:** isolated logs or dashboards provide complete security truth.
- **Policy input:** normalized event, asset/identity context, rule version, time window, confidence threshold.
- **Policy decision concept:** record, alert, require review, or forward a bounded response request.
- **Enforcement point:** alert/review workflow; no direct blocking by this pattern.
- **Telemetry:** source health, ingestion, correlation, alert, acknowledgment, false-positive disposition.
- **Expected control action:** supported patterns produce traceable alerts; missing evidence remains inconclusive.
- **Failure behavior:** surface collection/correlation failure and prevent unsupported automated action.
- **Rollback:** disable faulty rule, preserve source events, and restore last accepted rule set.
- **Validation method:** schema check, known-event positive/negative test, missing-source failure, repeated observation.
- **Evidence:** sanitized source/event map, correlation output, rule version, disposition and recovery.
- **Limitations:** no commercial SIEM, threat hunting, malware, packet payload, or enterprise behavior-analytics claim.
- **Candidate implementation technologies:** CANDIDATE ONLY — metrics/log collectors, open event schemas, rule-based correlation, dashboards.
- **Repository implementation status:** PLANNED.

## ZTP-AI-001 — Approval-gated reversible automation

- **Addressed capabilities:** ZT-3.2.1, ZT-7.6, ZT-8.1, ZT-8.2, ZT-8.3, ZT-8.4, ZT-8.5, ZT-8.6
- **Purpose:** turn a reliable, bounded decision into a deterministic action with explicit authority, audit, and rollback.
- **Trust assumption removed:** a detection or model score is sufficient authority for autonomous action.
- **Policy input:** accepted detection, confidence, asset/service criticality, approved action, operator authorization, rollback readiness.
- **Policy decision concept:** recommend, require approval, execute bounded action, or refuse.
- **Enforcement point:** controlled automation runner invoking an already-approved interface.
- **Telemetry:** input, decision, approver, action, outcome, rollback, residual risk.
- **Expected control action:** only allow-listed, approval-gated, reversible actions execute.
- **Failure behavior:** stop, preserve evidence, and revert or hand off to manual incident coordination.
- **Rollback:** mandatory tested rollback for each action; disable automation on uncertainty.
- **Validation method:** dry-run/static review, false-positive refusal, action failure, recovery, and adversarial input test.
- **Evidence:** sanitized input/decision/approval/action/rollback chain.
- **Limitations:** no autonomous defense, production SOAR, or AI intrusion-detection claim.
- **Candidate implementation technologies:** CANDIDATE ONLY — repository validators, signed change artifacts, approval gate, idempotent runbook executor.
- **Repository implementation status:** PLANNED.
