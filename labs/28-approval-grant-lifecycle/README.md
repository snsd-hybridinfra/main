# Lab 28: Approval, Access Grant and Expiration

**Status:** `MIGRATED / NOT_REVALIDATED`. Two complete source Python packages (`approval_api`, `grant_api`) and selected tests; they are not yet standalone runnable services.

## Question
Does the approval authority correctly constrain grant issuance, revocation and expiry while rejecting unauthorized or replayed requests?

## Contents
- `source/approval_api/`: policy, identity, approval state and provisioning hand-off
- `source/grant_api/`: grant lifecycle and expiry worker
- `reference/tests/`: approval, grant and authentication test sources

## Revalidation
Use synthetic request identities, expired grants and roles; stub identity provider, database and runner dependencies; test deny by default, replay, duplicate or revoked approval, expiration, audit event and race conditions. Do not use company identities or live providers.

The original PostgreSQL schema/migrations and API connections are not yet configured for this lab; passing source tests in the original repository does **not** imply they run here.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.


## Source packaging provenance
`reference/build/{approval-api,grant-api}/` preserves original service Dockerfiles and source notes. These are not an automatically integrated deployment.
