# ADR 0022: Managed Terraform Supply Chain

- Status: Accepted for local implementation
- Date: 2026-08-28
- Decision authority: operator direction to evolve `F:/2차프로젝트.zip` through a customized Terraform supply chain
- Architecture authority: `ZT-ARC-001`

## Context

The source archive supplied the original portal and AWS-oriented product-module
model. ADR 0012 adopted only its sanitized application structure and replaced
direct AWS products with bounded OpenStack execution profiles. The central IDP
now needs a stronger provisioning supply chain for approved composite
blueprints without exposing modules, provider identifiers or HCL to users.

Calling an unrestricted Terraform binary with a copied module is insufficient.
The runner must prove which source archive informed the implementation, which
catalog and module bytes were approved, which Terraform and provider artifacts
are used, and which resource actions appear in a saved plan before apply.

## Decision

Customize the Terraform execution layer, approved modules and policy gates; do
not fork Terraform core. The runner remains compatible with the upstream
Terraform CLI but wraps it with the repository-owned supply-chain contract:

```text
approved composite blueprint
  -> immutable resolved manifest
  -> approval decision
  -> locked internal execution profile
  -> module/catalog digest verification
  -> Terraform CLI and provider-package digest verification
  -> filesystem-only provider mirror
  -> saved plan JSON resource/action inspection
  -> apply the inspected plan
  -> post-apply state validation
  -> sanitized attestation and lifecycle decision
```

`applications/internal-iaas-portal/terraform/supply-chain-lock.json` is the
machine lock. It pins the sanitized source-archive digest, catalog digest,
Terraform CLI version, provider source/version, five module identities and
their content digests. Runtime binary and provider-package paths and digests
remain external inputs. The runner generates its own CLI configuration so the
provider can only be installed from the reviewed filesystem mirror.

Apply plans may contain only `create` or `no-op` actions for the exact resource
types and counts fixed by the execution profile. Destroy uses a saved destroy
plan and permits only `delete` or `no-op`. Replacement, update, import, read,
move, provider substitution, extra resources and direct registry installation
fail closed. The exact saved plan that passes inspection is the only plan that
may be applied.

## Consequences

- The source ZIP remains provenance, not a deployable or authoritative bundle.
- User-supplied HCL, module paths, provider identifiers and plan files remain denied.
- A catalog or module edit requires deliberate digest and regression updates.
- Real provisioning additionally requires external Terraform/provider artifacts and separate runtime authorization.
- The local mock path and this ADR provide no OpenStack runtime, production, compliance or Zero Trust status credit.
