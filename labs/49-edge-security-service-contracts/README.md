# Lab 49: Edge WAF, AuthN/AuthZ and Service API Contracts

**Status:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. Reference-only edge Nginx/ModSecurity policies, complete original interface/implementation docs (20 files), 11 previously unextracted integration/security/frontend tests, and IDP Docker Compose/MVP dependency contracts.

## Role: application edge and service security
Focus on session boundaries, external API callbacks, role-based access control, gateway and WAF allow/deny behavior, and untrusted request handling.

## Structure
- `reference/security/`: Nginx/ModSecurity edge and source smoke validation, **not activated**
- `reference/docs/`: interface and MVP implementation contracts
- `reference/applications/internal-iaas-portal/tests/`: source tests and frontend session cache examples; PowerShell scripts renamed inert `.reference.txt`
- `reference/applications/internal-iaas-portal/compose.mvp.yaml`: old multi-service composition **not executed**
- `reference/applications/internal-iaas-portal/zero-trust-protection-profile.yaml`: original intended protection contract

## Revalidation gates
1. Validate Nginx/ModSecurity configuration syntax with pinned images and a synthetic environment only.
2. Test HTTP denied/allowed, MFA/OIDC proxy trust, arbitrary header injection, session expiry, same-origin constraints and tenant isolation with fake users.
3. Check WAF false positives and bypasses. Default to deny for missing identity/evidence; validate authN and authZ at API not only gateway.
4. Use disposable mock API backends, no company identities, production DNS, real tokens or real customer data.
5. Do not treat imported tests or the source `compose.mvp.yaml` as proof of passing CI. Check dependencies and tests independently before running.

## Sources
`snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. See [Lab 27 Request API](../27-self-service-request-api/README.md), [Lab 28 Grant](../28-approval-grant-lifecycle/README.md) and [Lab 35 UI](../35-portal-ui-contracts/README.md). Imported-team Eclipse UI source remains excluded pending rights and provenance review.
