# Lab 33: EVE-NG Routing Model & Read-Only Assurance

**Status:** `MIGRATED / NOT_REVALIDATED`. Pure placeholder router configurations, topology and **reference-only** validation scripts were extracted; no EVE, customer equipment or device session was accessed.

## Goals
Build a management/bastion/transit/internal/monitoring routing model and validate routing intent, access boundaries, drift and safe evidence collection.

## Contents
- `source/eve-ng/`: placeholder-only routed-zones topology and router examples
- `source/ansible/inventories/`: synthetic multicloud inventory contract
- `reference/tools/live-validation/`: sanitizer and read-only validator **examples**; never execute remote scripts without explicit host/IP review, approved test user and sandbox
- `reference/ansible/`: access policy concept

## Next
Choose EVE-NG images you legally hold, substitute synthetic RFC1918 or documentation addressing, validate topology in isolation, test deny/allow and link failures, and redact all evidence. Do not copy workplace configurations.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
