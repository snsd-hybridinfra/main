# Local demonstration runbook

This runbook is local-only and must not be used as live deployment authorization.

## Preconditions

- Docker Compose is available.
- Strong, ephemeral `MVP_DB_PASSWORD` and `MVP_GRANT_SIGNING_KEY` values are set
  in the process environment and are not written to the repository.
- `RUNNER_MODE=mock` and `TF_OPENSTACK_DEPLOYMENT_AUTHORIZED=false` remain set.
- `TF_K3S_CONFIGURATION_AUTHORIZED=false` remains set.

## Demonstration

1. Start `compose.mvp.yaml` and wait for the database and approval API health
   checks.
2. Open the loopback-only user and administrator portals.
3. Request a VM product and verify `PENDING -> APPROVED -> PROVISIONING -> RUNNING`.
4. Request a k3s product and verify the catalog, private endpoint, PaaS scope, and
   sanitized `READY` mock result contain no token or kubeconfig.
5. Revoke or expire the Grant and verify access is blocked before
   `DESTROYING -> TERMINATED`.
6. Run the application tests and the static release-readiness check.

## Expected boundary

Application tests may pass locally. Release readiness must remain `NO-GO` while
container image digests, identity endpoints, private DNS names, external secrets,
OpenStack inputs, k3s bootstrap validation, and monitoring onboarding are not
accepted. Do not convert a mock result into runtime evidence.
