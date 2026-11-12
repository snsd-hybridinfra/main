# Blackbox Endpoint Probe Validation

This baseline validates symbolic service-availability probes and sanitized evidence without external queries in Static mode.

## Probe Model

`<blackbox-exporter>` applies `<probe-module-placeholder>` to `<endpoint-url-placeholder>` identified by `<endpoint-name-placeholder>`.

- HTTP 2xx expectation: `probe_success = 1` and `probe_http_status_code = <expected-status-code>` (200 or 204).
- TCP connect expectation: successful connection represented by `probe_success = 1`.
- Normal duration: `probe_duration_seconds <= 2.0`.
- Warning duration: greater than 2.0 and at most 5.0.
- Failure: greater than 5.0, timeout, refused connection, `probe_success = 0`, or unacceptable HTTP status.
- Timeout: `<probe-timeout-seconds>`; duration threshold: `<probe-duration-threshold-seconds>`.
- Evidence: `<evidence-path>`.

Endpoint lists contain placeholders only. Missing endpoint evidence fails unless an `<endpoint-name-placeholder>` is explicitly documented as intentionally disabled.

Static validation parses repository fixtures. Optional LiveBlackbox requires explicit exporter and target URLs, sends a credential-free probe request, and stores only sanitized metrics/status/timestamp, never URLs or raw response.
