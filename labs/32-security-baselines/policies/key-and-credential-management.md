# ZT-DATA-001 Key and Credential-Management Boundary

This package inventories categories and handling boundaries only. It does not
read, copy, rotate, revoke, back up, or recover any live credential or key.

| Category | Owner / storage class | Access, rotation, revocation, recovery, and audit boundary |
|---|---|---|
| Operator and validator SSH keys | Endpoint/operator owner; external user key store and target authorized-key boundary | Separate operator and forced-command validator identities; rotation/revocation is separately approved and must preserve recovery access; log metadata only |
| TLS certificates and private keys | Service owner; target-local secret store | Values prohibited from Git; renewal, revocation, and backup require service-specific rollback and evidence |
| OpenStack API/application credentials | OpenStack owner; external credential files or environment | Never inspect `clouds.yaml` or password stores; revoke/rotate through a separate OpenStack change |
| Database credentials | Application/data owner; external secret source | No connection secret is inventoried; backup must exclude plaintext credentials |
| Application secrets and tokens | Application owner; VM-local or platform secret boundary | Repository holds references/categories only; no token values, client secrets, or recovery material |
| Monitoring VM-local secret | Visibility owner; target-local restricted file | Used only by the accepted loopback stack; no value or unnecessary fingerprint is recorded |
| Data-encryption keys | Data owner and future key custodian; no current approved repository store | No production KMS, wrapping, escrow, rotation, or recovery is established by this package |
| MFA seeds and recovery codes | Identity owner; identity-provider/user secure boundary | Values are categorically excluded from repository, runtime evidence, backup fixture, and logs |

Repository-prohibited content includes private keys, passwords, tokens, client
secrets, API credentials, database connection secrets, MFA seeds, recovery
codes, live encryption keys, and unredacted secret findings. Audit evidence
records category, owner role, operation type, result, and sanitized reference,
never the value. Recovery procedures must prove independent operator access
before any future rotation or revocation.
