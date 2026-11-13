FROM alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8

RUN apk add --no-cache curl nginx openssh-client openssh-server

COPY edge-entrypoint.sh /usr/local/bin/edge-entrypoint.sh
RUN chmod 0755 /usr/local/bin/edge-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/edge-entrypoint.sh"]
