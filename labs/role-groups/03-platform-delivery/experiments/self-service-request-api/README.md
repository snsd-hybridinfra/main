# Lab 27: Self-Service Infrastructure Request API

**Status:** `SOURCE_MIGRATED / NOT_REVALIDATED`. All 20 `request_api/` Python modules plus selected tests, requirements and product schema references were extracted; this is **not a runnable standalone web service yet**.

## Goal
Study the boundary between catalog/blueprint selection, request submission, identity validation, policy, provisioning job state, and lifecycle.

## Contents
- `source/request_api/`: original application package including request, catalog, schema, policy, agent and internal integration modules
- `reference/`: test source, dependency list, composite product catalog and private IaaS golden-path reference
- **Not imported into this lab:** original PostgreSQL migrations and sibling approval/grant/runner services. Lab 28–29 will preserve those dependencies separately.

## Before execution
1. Build a non-networked, synthetic database fixture with explicit migration versions.
2. Stub approval/grant, identity provider, Terraform runner, and LLM/integration clients; ensure fail-closed authorization.
3. Test invalid requests, missing approval, duplicate submission, partial failure, role escalation and cancellation.
4. Use fake accounts, fake order/finance data and dummy domain names only. **Do not deploy the original API with its default configuration.**
5. Claim successful local validation only after tests and sanitized evidence are recorded.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `applications/internal-iaas-portal/services/request-api/`.


## Source packaging provenance
`reference/build/request-api/` preserves the old Dockerfile and short service notes. It is **not** a tested standalone container build context.
