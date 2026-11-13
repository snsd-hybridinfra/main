
# Host-Onboarding Contract

The common contract runs after provider-specific provisioning or registration and before Configuration as Code deployment.

Required checks cover supported OS and architecture, reachability, approved SSH, bounded privilege escalation, absence of unrestricted sudo, time, DNS, storage and filesystem capacity, interfaces, internal network, public exposure, package manager, Python where required, rollback path, runtime directory, and evidence directory.

Allowed results are `READY`, `READY_WITH_WARNINGS`, `NOT_READY`, `BLOCKED`, and `REVIEW_REQUIRED`. `NOT_READY` and `BLOCKED` deny Configuration as Code deployment. Warnings and review conditions require recorded approval before progression.

The machine contract is `host-onboarding-contract.yaml` and is validated against `schemas/zero-trust-host-onboarding-contract.schema.json`.
