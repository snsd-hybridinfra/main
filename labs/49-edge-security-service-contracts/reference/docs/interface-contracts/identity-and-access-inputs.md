# Identity and access inputs

Production mode requires an approved OIDC issuer, audience, JWKS URL, role and
scope claims, administrator MFA, service OAuth clients, TLS trust bundles, and
a PEP route that prevents direct browser access to backend APIs.

Roles remain separated: requester, approver, Grant administrator, auditor, and
runner service. A requester cannot approve the same request. User-supplied Grant
scopes are ignored; scopes come from the fixed product policy.

The current Compose demo uses development headers and is loopback-only. It is
not an identity implementation or runtime evidence. The Kubernetes candidate
uses OIDC mode but contains placeholder image and endpoint values and is not
authorized for deployment.

The target browser origins are `https://gg-snsdinfra.cloud` for users and
`https://admin.gg-snsdinfra.cloud` for restricted administrators. The target
issuer is `https://id.gg-snsdinfra.cloud/realms/iaas`. DNS records, exact-name
TLS certificates, Keycloak hostname configuration and exact redirect URIs must
be validated together before enabling production authentication.

The monitoring assistant uses the human OIDC session only for portal role and
scope enforcement. External model calls use a separate server-side OpenAI
Platform service credential in the optional `monitoring-assistant-provider`
secret. Browser cookies, personal ChatGPT sessions and user-supplied API keys
must never be forwarded to the provider.
