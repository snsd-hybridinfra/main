# Load Balancing Health Check Validation

This baseline validates a non-production backend-health model without configuring or contacting a load balancer in Static mode.

## Purpose and Request Path

`Client -> Load Balancing Layer -> Healthy Backend Service`

`<load-balancer>` routes to `<backend-pool>`, which contains `<backend-service-a>` and `<backend-service-b>`. Each backend exposes `<backend-health-path>` and is expected to return `<expected-status-code>` when healthy.

## Health Model

- Health endpoint: `<backend-health-path>`
- Expected healthy response: `<expected-status-code>`
- Unhealthy response handling: mark the observation unhealthy and exclude the backend through a separately approved/manual operational action.
- Health check interval: `<health-check-interval>`
- Health check timeout: `<health-check-timeout>`
- Retry threshold: `<unhealthy-threshold>`
- Failure threshold: `<unhealthy-threshold>`
- Backend removal / marking-unhealthy behavior: `<unhealthy-threshold>` consecutive failures require review before exclusion.
- Manual recovery / failover relationship: restore and re-admit a backend only after evidence confirms health.

The Nginx example models open-source passive upstream retry using `proxy_next_upstream` plus explicit backend health endpoint evidence. It does not claim Nginx Plus active health checking, automatic backend removal, or production-grade automatic failover.

## Evidence Collection Model

Static validation parses repository artifacts and sanitized samples under `<evidence-path>`. Optional live HTTP health check validation runs only with explicit `-LiveHttp`, `-LoadBalancerHealthUrl`, and `-BackendHealthUrls`. It sends cookie-free, credential-free HEAD requests and stores only indexed status codes and a timestamp, never URLs, headers, or bodies.

## Validation Modes

- **Static validation:** default; does not run curl, Nginx, or any network request.
- **Optional live HTTP health check validation:** explicit operator action against approved URLs; does not change configuration or perform failover.
