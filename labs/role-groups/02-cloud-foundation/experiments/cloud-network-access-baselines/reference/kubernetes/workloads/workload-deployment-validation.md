# Kubernetes Workload Deployment Validation

This document defines repository-side workload validation for a non-production sample in `<namespace>`.

## Validation Purpose

- Required workload object: `Deployment`.
- Required service object: `Service`.
- Required namespace object: a dedicated namespace definition.
- Require available replicas to match the desired `<replica-count>`.
- Require workload pods to report Ready and Running.
- Use `<container-image-placeholder>` or an approved fixed non-latest example image.
- Keep Deployment labels, pod-template labels, Service selectors, `<deployment-name>`, and `<service-name>` consistent.
- Require readiness and liveness probes for `<container-name>`.
- Require resource requests and limits.
- Reject host networking, privileged containers, hostPath, Secret resources, image-pull secrets, and unintended NodePort exposure.

## Evidence Collection Model

- Default static mode parses manifests and non-production sample output under `<evidence-path>` without running kubectl.
- Optional `LiveKubectl` mode runs only read-only deployment and pod listing in `snsd-example`.
- Live evidence stores aggregate readiness, availability, running, failure, and restart counts rather than raw workload names or cluster details.

## Static and Live Distinction

Static manifest validation proves repository structure and parser behavior. Optional live validation observes workload state but does not apply, delete, patch, edit, or otherwise modify Kubernetes resources.
