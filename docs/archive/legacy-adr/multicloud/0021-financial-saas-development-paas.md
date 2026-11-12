# ADR-0021: Model Financial SaaS Development as an IDP Composite PaaS Product

## Status

Accepted for bounded local implementation on 2026-08-28.

## Context

The target architecture is an Internal Developer Platform that presents approved
IaaS and PaaS products through a self-service portal. A financial SaaS
development environment is therefore not a single application and is not the
Mini-Ona sandbox. It is a governed composite product assembled from hidden
platform components and resolved into an immutable manifest.

The current service plane is OpenStack plus k3s. Public-cloud adapters remain
deferred, so the operating claim stays `Hybrid-Ready`.

## Decision

- Retain eight user-facing approved blueprints.
- Specialize `API_DEVELOPMENT_STACK` as the **Financial SaaS Development PaaS**.
- Keep Kubernetes, application runtime, PostgreSQL, Redis, message queue,
  object storage, ingress, network policy and operations as internal components.
- Accept only blueprint, environment, size, duration and purpose from users.
- Resolve all internal choices server-side and bind the result to a canonical
  SHA-256 manifest digest.
- Limit the product to synthetic or non-production data in `DEV`, `TEST` and
  `STG`.
- Keep Mini-Ona as a separate internal automation service. Kata isolation is
  required for Mini-Ona's untrusted execution pods, not for ordinary SaaS
  application workloads.
- Separate cluster bootstrap, platform add-ons and tenant application delivery.
- Require explicit approval before runtime mutation and preserve reverse-order
  rollback and TTL-based destruction.

## Consequences

The portal remains simple while the platform can evolve adapters independently.
The initial repository slice may validate catalog and manifest behavior without
claiming that PostgreSQL, Redis, messaging, storage, identity or observability
are integrated. A public-cloud provider, production financial data, multi-site
DR and production readiness remain excluded.
