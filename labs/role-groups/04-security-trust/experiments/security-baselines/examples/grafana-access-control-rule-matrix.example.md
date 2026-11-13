# Grafana Access Control Rule Matrix Example

NON-PRODUCTION EXAMPLE: this matrix documents static access-control expectations and does not configure Grafana.

| Control Area | Required Setting | Approved Value | Forbidden Value | Purpose | Validation Method | Evidence Reference |
|---|---|---|---|---|---|---|
| Anonymous access | `[auth.anonymous] enabled` | false | true or environment override true | Require authentication | Static section/value check | retired-numbered-case |
| Anonymous org role | `org_role` | Viewer is non-effective while anonymous is disabled | live anonymous Viewer access | Prevent unauthenticated dashboard viewing | Policy and config review | retired-numbered-case |
| Admin password storage | `admin_password` | `<managed-outside-repository>` | committed password value | Keep admin credentials external | Placeholder-only assignment check | retired-numbered-case |
| API token storage | API token policy | no token stored | token-like value | Keep automation credentials external | Token pattern scan | retired-numbered-case |
| Datasource credential storage | datasource authentication | no credential stored | password, token, secureJsonData value | Protect datasource access | Credential pattern scan | retired-numbered-case |
| Public dashboard exposure | public sharing policy | separate documented justification | baseline public exposure | Prevent unintended public dashboards | Policy review | retired-numbered-case |
| Authenticated viewer access | viewer role | `<authenticated-viewer-role>` | anonymous Viewer | Assign least-privilege viewing | Policy review | retired-numbered-case |
| Dashboard sharing control | sharing scope | authenticated and reviewed | unrestricted anonymous sharing | Control redistribution | Policy review | retired-numbered-case |
