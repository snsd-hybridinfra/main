# Lab 18: Bounded Observability (Grafana / Loki / Alloy)

**Status:** `MIGRATED / NOT_REVALIDATED`. Container/runtime and current image versions have **not** been checked in the destination lab.

## Goal
Collect only pre-sanitized synthetic JSONL logs, expose dashboards on loopback, and test read/query, persistence, retention, and denial of anonymous access. This is not an NMS device collector or a verified production monitoring stack.

## Contents
- `compose.yaml`: Loki + Alloy + Grafana, local Docker network, localhost-bound published ports
- `alloy-config.alloy`: only `input/sanitized/*.jsonl` accepted, no general host log mounts
- `loki-config.yaml`: local TSDB and 14-day configured retention
- `grafana-provisioning/datasources/loki.yaml`: Grafana datasource

## Local setup (manual, **not yet executed**)
1. Create `.secrets/grafana_admin_password` with an independently generated password, restrict access (for example `chmod 600`). Never commit it.
2. Create `input/sanitized` and `.state/{loki,alloy,grafana}` directories. Supply **synthetic** log lines only; the path must not contain workplace logs or identifiers.
3. Review image digests/versions and container permissions before starting; upstream versions in the original source are historical pins, not recommendations for the latest versions.
4. Run `docker compose config` before `docker compose up -d` in a disposable local machine. The stack only publishes loopback ports (3100, 12345, 3000).
5. Check collection, Loki query, Grafana login denial, persistence after container recreation and retention behavior with sanitized evidence.
6. Stop via `docker compose down`, **without** `-v` or deleting `.state` while data are still needed.

## Security considerations
- Loki's `auth_enabled: false` is for an isolated local lab network, **not** public exposure; do not port-forward externally.
- Grafana localhost HTTP is not TLS; use only local loopback access in this lab.
- Alloy runs as root in the original container configuration; evaluate whether a nonroot UID can read the synthetic directory before any broader use.
- The pinned container images may be out of date or unavailable. Do not imply they were pulled or security-reviewed.

## Source and future use
Adapted from `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`, `observability/logging/`. Only repo-local example paths and neutral project naming were changed. Future combination: network event logging, synthetic topology validation events, and failure/restore evidence.
