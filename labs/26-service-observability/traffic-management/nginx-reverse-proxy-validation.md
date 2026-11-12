# Nginx Reverse Proxy Validation

This baseline defines repository-side validation for a non-production Nginx reverse proxy example. It does not configure, start, reload, or connect to Nginx in Static mode.

## Purpose and Request Path

The validated request path is:

`Client -> Nginx Reverse Proxy -> Backend Service`

The model requires an `upstream` block for `<upstream-name>`, a `server` block for `<public-service-domain>`, and a `location` block that uses `proxy_pass` to route to `<backend-service>` on `<backend-service-port>`.

## Forwarding Baseline

- Preserve the client Host value with `proxy_set_header Host $host`.
- Forward the source address placeholder with `proxy_set_header X-Real-IP $remote_addr`.
- Extend the proxy chain placeholder with `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for`.
- Preserve the original scheme placeholder with `proxy_set_header X-Forwarded-Proto $scheme`.
- Define `proxy_connect_timeout`, `proxy_send_timeout`, and `proxy_read_timeout` explicitly.
- Document `<backend-health-path>` for later, explicitly approved HTTP validation.
- Use `<reverse-proxy-host>` only as an operator-supplied placeholder; never commit its resolved value.

Nginx response security headers are owned by retired-numbered-case and are not revalidated here.

## Placeholder Contract

Only these symbolic values are used in the design:

- `<reverse-proxy-host>`
- `<public-service-domain>`
- `<backend-service>`
- `<backend-service-port>`
- `<backend-health-path>`
- `<upstream-name>`
- `<evidence-path>`

## Evidence Collection Model

Static validation reviews the baseline, marked example configuration, command reference, rule matrix, and sanitized sample evidence. Results are written beneath `<evidence-path>` as a generated log and Markdown summary.

Optional live HTTP validation runs only when both `-LiveHttp` and an operator-supplied `-TargetUrl` are provided. It sends a credential-free HEAD request, stores only a sanitized status code and timestamp, and never stores the target URL, response body, cookies, authorization headers, or other response headers.

## Validation Modes

- **Static config validation:** default; does not run Nginx, curl, or any network request.
- **Optional live HTTP validation:** explicit `LiveHttp` mode; performs one safe HEAD request and does not modify or reload Nginx.
