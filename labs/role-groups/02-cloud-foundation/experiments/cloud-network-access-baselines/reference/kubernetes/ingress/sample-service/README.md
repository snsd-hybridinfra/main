# Sample Service Ingress

NON-PRODUCTION EXAMPLE for retired-numbered-case static routing validation.

- Namespace: `snsd-example`
- Host: `app.example.internal`, reserved for local documentation
- Path: `/` with `Prefix`
- Backend: `sample-service-placeholder:80`
- Ingress class: `nginx`
- TLS: `<tls-secret-placeholder>` is documented but no Secret or TLS material is defined
- No wildcard host, endpoint URL, public IP, certificate, or private key

Do not apply this example without a separate implementation review.
