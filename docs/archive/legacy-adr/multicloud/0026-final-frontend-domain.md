# ADR 0026 Final Frontend Domain

## Status

Accepted as the deployment target. DNS, TLS and OIDC runtime validation remain `NOT_VALIDATED`.

## Decision

Use `https://gg-snsdinfra.cloud` as the canonical user-facing portal URL. Reserve `https://admin.gg-snsdinfra.cloud` for the restricted administration frontend and `https://id.gg-snsdinfra.cloud` for the organization identity endpoint.

The user has asserted ownership of the parent domain. Ownership assertion is not DNS or certificate evidence. Deployment requires explicit DNS records, a certificate covering the three exact names, HTTPS-only routing and OIDC redirect URIs that exactly match the canonical origins. Wildcard DNS, direct backend exposure and alternate production origins are not part of this decision.
