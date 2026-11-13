# ZT-VIS-002 OpenStack environment candidate

This root module wires the reviewed `ZT-VIS-002` private monitoring VM module to
the existing OpenStack provider. Runtime values and authentication must resolve
through protected external `terraform.tfvars` and `clouds.yaml` files; neither
belongs in this repository.

The separately authorized 2026-08-21 control-node preflight ran backend-disabled
`init`, `validate`, and no-apply `plan` and recorded only sanitized structural
evidence. Do not re-run that preflight or run `apply` from repository
automation. Applying the protected saved plan requires a separate authorization
bound to its recorded fingerprint, refreshed artifact checks, an approved state
boundary, and the rollback checkpoint.
