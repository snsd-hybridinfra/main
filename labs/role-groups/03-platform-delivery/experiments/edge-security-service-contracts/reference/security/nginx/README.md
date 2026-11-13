# Edge candidate

This directory contains a local reverse-proxy and WAF candidate for the user,
administrator, and identity routes. It does not configure the repository's
authoritative identity provider or PEP.

`IDENTITY_UPSTREAM` and all public names remain deployment inputs. They may be
set only after the ZT-ID-001 and ZT-APP-001 owners approve the identity, route,
certificate, and upstream contracts. Direct API exposure is not an accepted
production topology.
