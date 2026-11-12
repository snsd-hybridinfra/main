# Grafana Anonymous Access Denial Baseline

This repository-side baseline defines non-production access-control intent only. It does not connect to or configure Grafana.

## Mandatory Access Controls

- Anonymous access must be disabled.
- Grafana dashboards must require authenticated access.
- Viewer access is assigned through an authenticated user, team, or role model such as `<authenticated-viewer-role>`.
- Anonymous Viewer role must not be enabled and `org_role = Viewer` is non-effective while anonymous access remains disabled.
- Grafana admin password must not be stored in repository files.
- Grafana API tokens must not be stored in repository files.
- Datasource credentials must not be stored in repository files.
- Public dashboard exposure requires separate justification outside this baseline.
- `<grafana-admin-user-placeholder>` is an identity placeholder, not a credential.
- `<grafana-host>`, `<grafana-url-placeholder>`, and `<grafana-config-path>` identify documentation concepts only.

## Evidence Collection Model

- Run the local validator without starting Grafana or reading environment values.
- Store sanitized evidence below `<evidence-path>`.
- Record stable check IDs for policy, matrix, config, denial settings, credential safety, and execution boundaries.
- Reject passwords, tokens, datasource credentials, real URLs, addresses, private material, and account-specific values.

## Static Validation Limitation

This validation confirms repository intent only. It does not prove live login enforcement, dashboard permissions, sharing behavior, datasource access, or production security.

