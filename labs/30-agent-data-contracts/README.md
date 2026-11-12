# Lab 30: Agent Sandbox & Data Exchange Contracts

**Status:** `SOURCE_MIGRATED / NOT_REVALIDATED`. These are **architecture contracts and source tests**, not a connected AI agent or a working NAS integration.

## Source material
- `contracts/`: agent isolation/readiness, NAS exchange, monitoring helper, synthetic financial SaaS and securities-domain boundaries
- `reference/tests/`: tests for agent orchestration, runtime adapters, NAS, monitoring, financial SaaS and sandbox policy
- Related implementation components are preserved in [Lab 27](../27-self-service-request-api/README.md) (`request_api/agent_*.py`, `nas_exchange.py`, `monitoring_assistant.py`, `saas_paas.py`). Avoid duplicating large service files.

## Proposed lab stages
1. Run policy and contract schema checks on synthetic inputs (no external LLM and no live network).
2. Test denied file paths, denied tool scope, expired authority, unsupported destinations and failed budget gates.
3. Mock NAS checksum/staging, consent/approval and in-memory database transactions. Record negative test outcomes.
4. Only after independent isolation review connect non-production external services.

**Do not import** real customer records, market data, brokerage APIs, secrets, or operational logs.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
