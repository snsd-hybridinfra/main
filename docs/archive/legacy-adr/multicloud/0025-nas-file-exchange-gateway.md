# ADR 0025 NAS File Exchange Gateway

## Status

Accepted with a metadata-only local state-machine simulation. Runtime NAS,
scanner, SMB and identity validation remains `NOT_VALIDATED`.

## Context

The supplied legacy project report describes a Synology NAS based internal and external network exchange flow using shared storage, SMB3 encryption, upload inspection, extension and keyword blocking, folder permissions, CIFS port restriction, source network allow lists and protected administration.

Directly mounting one writable share in both network zones would weaken the current separation model. Static randomly generated user passwords are also replaced by organization identity, short-lived grants and service identities.

## Decision

Reuse the report's security objectives through a dual-stage NAS exchange gateway:

1. An external-zone drop share accepts bounded synthetic or sanitized files over SMB 3.1.1 with encryption and signing required.
2. A transfer worker moves an immutable copy into quarantine. No client can write directly to the internal delivery share.
3. Malware, archive-depth, file-type, extension, content-policy and size checks run before approval. A rejection preserves only bounded audit metadata and quarantines or deletes content according to retention policy.
4. An authorized reviewer approves a digest-bound file. The gateway copies the approved object to a separate internal read-only delivery share.
5. Every transition is linked by exchange ID, digest, policy decision, actor, timestamps and final expiry. Credentials and file contents are never committed to Git or exported to the LLM monitoring assistant.

The NAS capability is an internal component of existing approved composite blueprints. It is not a ninth user-selectable product and does not permit free-form shares or protocols.

The local simulator accepts only digest, byte count, declared/detected bounded
types, boolean scan verdicts, archive depth, scan latency, opaque actor
references and timezone-qualified timestamps. It never receives a filename,
file body or raw scanner output and never mounts or copies a file. It proves
transition, rejection, separation-of-duty, MFA, digest binding, expiry and
numeric metric contracts only; it is not runtime evidence for a NAS appliance.

## Constraints

- Never expose SMB to the public Internet.
- Never mount one writable volume in both trust zones.
- Disable SMB1 and SMB2; require SMB 3.1.1 encryption and signing.
- Permit only approved source networks and the minimum SMB and management paths.
- Keep management on an isolated interface with MFA and audited break-glass access.
- Reject active content by default until an explicit policy permits it.
- Use synthetic or sanitized non-production data only.
- Do not claim a hardware data diode, multi-site DR or production financial transfer.
