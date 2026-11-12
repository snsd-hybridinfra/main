# Nginx Reverse Proxy Rule Matrix Example

NON-PRODUCTION EXAMPLE. All values are symbolic placeholders.

| Reverse Proxy Control | Required Directive | Approved Placeholder Value | Purpose | Failure Condition | Validation Method | Evidence Reference |
|---|---|---|---|---|---|---|
| upstream backend definition | `upstream` | `<upstream-name>` with `<backend-service>:<backend-service-port>` | Define the backend pool | Upstream block or symbolic backend is missing | Static config review | `<evidence-path>` |
| server listen directive | `listen` | `80` | Define the example listener | Listen directive is missing | Static config review | `<evidence-path>` |
| server_name placeholder | `server_name` | `<public-service-domain>` | Define symbolic virtual host selection | Real domain or missing placeholder | Static config review | `<evidence-path>` |
| location routing | `location` | `/` | Match the example request path | Location block is missing | Static config review | `<evidence-path>` |
| proxy_pass | `proxy_pass` | `http://<upstream-name>` | Forward to the named upstream | Proxy target is missing or broad | Static config review | `<evidence-path>` |
| Host forwarding | `proxy_set_header Host` | `$host` | Preserve the request Host | Host is overwritten or omitted | Static config review | `<evidence-path>` |
| X-Real-IP forwarding | `proxy_set_header X-Real-IP` | `$remote_addr` | Forward the source-address placeholder | Header is omitted | Static config review | `<evidence-path>` |
| X-Forwarded-For forwarding | `proxy_set_header X-Forwarded-For` | `$proxy_add_x_forwarded_for` | Preserve the proxy chain | Header is omitted | Static config review | `<evidence-path>` |
| X-Forwarded-Proto forwarding | `proxy_set_header X-Forwarded-Proto` | `$scheme` | Preserve the original scheme | Header is omitted | Static config review | `<evidence-path>` |
| proxy_connect_timeout | `proxy_connect_timeout` | `<timeout-value>` | Bound upstream connection time | Timeout is missing | Static config review | `<evidence-path>` |
| proxy_send_timeout | `proxy_send_timeout` | `<timeout-value>` | Bound upstream send time | Timeout is missing | Static config review | `<evidence-path>` |
| proxy_read_timeout | `proxy_read_timeout` | `<timeout-value>` | Bound upstream response time | Timeout is missing | Static config review | `<evidence-path>` |
| backend health path placeholder | health path reference | `<backend-health-path>` | Define a future health request path | Health path placeholder is absent | Documentation review | `<evidence-path>` |

