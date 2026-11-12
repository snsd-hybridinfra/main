# Kubernetes Node Readiness Validation

This document defines the node-readiness evidence model for `<kubernetes-cluster>` without embedding cluster access data.

## Validation Purpose

- Confirm every evaluated node reports the required condition `Ready=True` or the equivalent `Ready` status.
- Treat `NotReady` as a validation failure requiring investigation before workload operations continue.
- Treat `SchedulingDisabled` as a warning unless expected maintenance is explicitly documented.
- Recognize kubelet readiness as the node-local signal surfaced through the Kubernetes node condition.
- Distinguish `<control-plane-node>` and `<worker-node>` roles while applying the same readiness requirement.
- Record `<node-name>`, `<node-role>`, and `<node-readiness-condition>` only as placeholders in repository documentation.

## Evidence Collection Model

- Default mode parses non-production captured evidence under `<evidence-path>` and never runs kubectl.
- Optional `LiveKubectl` mode is explicit and runs only read-only `kubectl get nodes --no-headers`.
- Live output is reduced to status counts; kubeconfig paths, tokens, certificates, endpoints, addresses, and raw node details are not stored.
- Any `NotReady` result fails validation. `SchedulingDisabled` remains visible as a warning.

## Static and Live Distinction

Static evidence validation proves the repository model and parser behavior. Optional live validation observes current node statuses but does not apply, delete, patch, cordon, drain, taint, edit, or otherwise modify cluster resources.

