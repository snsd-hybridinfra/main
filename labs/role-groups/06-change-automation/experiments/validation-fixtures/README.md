# Lab 37: Validation Harness and Synthetic Test Fixtures

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. All **36 source files** under the previous repository's `tests/` tree were copied as test references. No tests have been run since migration.

## Goal
Preserve synthetic inputs, negative cases and regression tests for the extracted network, cloud, governance, telemetry and Zero Trust labs.

## Scope
- `reference/fixtures/`: synthetic telemetry, invalid inputs and policy fixtures.
- `reference/test_*.py`: original platform/Zero Trust/automation/security test scripts. Their imports and root path assumptions often require source packages and original catalog files that are *not present here*.

## How to use it
1. Classify import and fixture dependencies by target lab.
2. Refactor each test into an isolated unit or integration test with synthetic fixtures and mocked API calls.
3. Run only after reviewing subprocess, file writes, remote access and cloud dependencies.
4. Preserve explicit PASS/FAIL/BLOCKED and negative control results. Tests from the old repository do not establish new lab success.

A source test for redaction intentionally includes the **literal header marker** `-----BEGIN PRIVATE KEY-----` as a short synthetic string, not a private key payload.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `tests/`.
