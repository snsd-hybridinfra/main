
# Limitations

- ZT-ARC-001 is architecture and local validation only.
- Capability implementation, validation, evidence authority, and maturity remain separate.
- The current baseline stays `UNASSESSED` for all 52 capabilities.
- ZT-VIS-001 establishes one validated Grafana/Loki/Alloy stack for approved sanitized JSONL. ZT-VIS-002 is partially runtime accepted for one private OpenStack five-component monitoring VM at EC3; alert delivery, elapsed retention, full Cinder snapshot restore, broader onboarding, high availability, and production operation remain unvalidated, and `.runtime` traces remain non-authoritative.
- Keycloak, OIDC, MFA, role mapping, and protected Grafana access are not implemented by this task.
- Existing VM and physical-server adapters do not provision compute or hardware.
- AWS, Azure, Kubernetes, and additional OpenStack adapters remain roadmap-only.
- No automatic remediation is enabled.
- Device posture, behavior risk, continuous adaptive authorization, and dynamic risk are unavailable or future signals.
- Runbooks are design specifications until clean-operator and runtime tests exist.
- No overall maturity score is produced.
