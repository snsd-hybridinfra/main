# Lab 29: OpenStack Terraform Blueprints & Job Runner

**Status:** `SOURCE_MIGRATED / NOT_REVALIDATED`. Full five-source-module Terraform blueprint catalog and original `terraform_runner` Python package were copied as independent source assets, with selected tests. They **have not been integrated or executed** in this lab.

## Topics
- Blueprint sizing and configuration (small/medium/large VM, small/medium k3s)
- Catalog-driven provisioning request, policy approval, job dispatch, locking and rollback rules
- Terraform source integrity and runner restrictions

## Exclusions and guardrails
- No provider credentials, state/backend contents, actual VM identity, live OpenStack or CI runner.
- Original service expects databases, policy and cross-service APIs in the old repository; tests cannot be presumed to pass after relocation.
- **Do not execute `terraform_runner/executor.py` or Terraform apply/destroy** without an independently reviewed isolated OpenStack tenant, explicit resource allowlist, policy checks and a rollback plan.

## Lab revalidation
First static `fmt/validate` per module and check product inputs, then deterministic dry-run job state transitions, guardrail denials, unknown-state recovery and verified idempotency. Preserve redacted results.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
