FROM alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8

RUN apk add --no-cache openssh-client openssh-server openssl python3 sshpass

COPY device-entrypoint.sh /usr/local/bin/device-entrypoint
COPY mock-cli.sh /usr/local/bin/mock-cli
COPY device_server.py /opt/mock/device_server.py
COPY fixtures /opt/mock/fixtures

RUN chmod 0755 /usr/local/bin/device-entrypoint /usr/local/bin/mock-cli

ENTRYPOINT ["/usr/local/bin/device-entrypoint"]
