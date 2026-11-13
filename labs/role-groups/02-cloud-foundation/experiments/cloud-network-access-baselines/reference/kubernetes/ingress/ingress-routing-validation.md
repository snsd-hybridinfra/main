# Kubernetes Ingress Routing Validation

This document defines repository-side routing validation for a non-production Ingress in `<namespace>`.

## Validation Purpose

- Validate the request path: Client -> Ingress Controller -> Ingress Rule -> Service -> Pod.
- Require an `Ingress` object named through `<ingress-name>`.
- Require a Service backend reference using `<service-name>` and `<service-port>`.
- Require `<host-placeholder>` and `<path-placeholder>` route definitions.
- Require namespace alignment between Ingress and backend Service.
- Require an `<ingress-class>` value.
- Keep `<pod-selector>` consistent with the backend Service and workload model.
- Match the Ingress backend port to the Service port.
- Treat `<tls-secret-placeholder>` as documentation only; do not store or create certificate or private-key material.

## Evidence Collection Model

- Default static mode parses the manifest and non-production ingress/describe/endpoint samples under `<evidence-path>` without running kubectl or curl.
- Optional `LiveKubectl` mode runs only read-only Ingress, Service, and Endpoints queries in `snsd-example`.
- Live evidence stores counts and routing judgments rather than raw names, addresses, certificates, or cluster details.

## Static and Live Distinction

Static manifest validation proves repository routing intent. Optional live validation observes resource availability but does not apply, delete, patch, edit, or otherwise modify resources and never runs HTTP validation automatically.

