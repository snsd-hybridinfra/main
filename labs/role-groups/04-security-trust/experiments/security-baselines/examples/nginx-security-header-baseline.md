# Nginx Security Header Baseline

This repository-side baseline defines a non-production reverse-proxy header policy. It does not configure or contact Nginx.

## Required Security Headers and Directives

- Server token exposure is reduced with `server_tokens off;` to limit Nginx version disclosure.
- `X-Frame-Options` uses `SAMEORIGIN` to reduce clickjacking risk.
- `X-Content-Type-Options` uses `nosniff` to prevent MIME-type sniffing.
- `Referrer-Policy` uses `strict-origin-when-cross-origin` to constrain referrer disclosure.
- `Content-Security-Policy` uses `<content-security-policy-placeholder>` until a service-specific policy is reviewed.
- `Strict-Transport-Security` uses a placeholder baseline at `<tls-termination-point>` and must be enabled only after HTTPS behavior is verified.
- `Permissions-Policy` uses `<permissions-policy-placeholder>` until service permissions are reviewed.
- `X-XSS-Protection` is a legacy compatibility header and is not a substitute for Content Security Policy or output encoding.
- Security `add_header` directives use `always` so expected error responses receive the baseline headers.

## Scope Placeholders

The policy applies to `<public-service-domain>` on `<reverse-proxy-host>` forwarding to `<backend-service>`. These are documentation placeholders only.

## Header Validation Evidence Model

- Run the local validator and store sanitized output below `<evidence-path>`.
- Record stable check IDs for the baseline, matrix, config, required values, and safety checks.
- Do not store domain names, server addresses, TLS keys, certificates, credentials, or account-specific values.

## Limitations of Static Config Validation

Static validation confirms repository intent only. It does not prove active Nginx configuration, inheritance behavior, response headers, TLS correctness, upstream behavior, or production security.
