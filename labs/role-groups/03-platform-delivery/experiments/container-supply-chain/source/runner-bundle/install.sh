#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) -eq 0 ]] || { echo "runner bundle installation requires root" >&2; exit 77; }
id idprunner >/dev/null 2>&1 || { echo "idprunner account is missing" >&2; exit 69; }

install -d -m 0755 /usr/local/bin /usr/local/lib/docker/cli-plugins /usr/local/sbin
for binary in containerd containerd-shim-runc-v2 ctr docker docker-init docker-proxy dockerd runc; do
  install -o root -g root -m 0755 "$root/payload/docker/$binary" "/usr/local/bin/$binary"
done
install -o root -g root -m 0755 "$root/payload/docker-buildx" /usr/local/lib/docker/cli-plugins/docker-buildx
install -o root -g root -m 0755 "$root/payload/trivy" /usr/local/bin/trivy
install -o root -g root -m 0755 "$root/payload/syft" /usr/local/bin/syft
install -o root -g root -m 0755 "$root/payload/cosign" /usr/local/bin/cosign
install -o root -g root -m 0755 "$root/payload/gh" /usr/local/bin/gh
install -o root -g root -m 0755 "$root/payload/git" /usr/local/bin/git
install -o root -g root -m 0755 "$root/idp-egress-policy-apply" /usr/local/sbin/idp-egress-policy-apply
install -o root -g root -m 0755 "$root/idp-egress-policy-check" /usr/local/sbin/idp-egress-policy-check

rm -rf -- /opt/actions-runner
install -d -o root -g root -m 0755 /opt/actions-runner
tar --extract --gzip --file "$root/payload/actions-runner.tar.gz" --directory /opt/actions-runner --no-same-owner
find /opt/actions-runner -type d -exec chmod 0755 {} +
find /opt/actions-runner -type f -exec chmod go-w {} +
chmod 0755 /opt/actions-runner/run.sh /opt/actions-runner/config.sh /opt/actions-runner/bin/Runner.Listener

getent group docker >/dev/null || groupadd --system docker
usermod -a -G docker,proxy idprunner
install -d -o idprunner -g idprunner -m 0700 /home/idprunner/.docker
cat >/home/idprunner/.docker/config.json <<'JSON'
{
  "proxies": {
    "default": {
      "httpProxy": "http://172.17.0.1:3128",
      "httpsProxy": "http://172.17.0.1:3128",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
JSON
chown idprunner:idprunner /home/idprunner/.docker/config.json
chmod 0600 /home/idprunner/.docker/config.json

install -d -m 0755 /etc/docker /etc/systemd/system/docker.service.d
cat >/etc/docker/daemon.json <<'JSON'
{
  "icc": false,
  "live-restore": true,
  "no-new-privileges": true,
  "userland-proxy": false,
  "log-driver": "local",
  "log-opts": {"max-size": "10m", "max-file": "3"}
}
JSON
cat >/etc/systemd/system/containerd.service <<'UNIT'
[Unit]
Description=containerd container runtime
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/containerd
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
UNIT
cat >/etc/systemd/system/docker.service <<'UNIT'
[Unit]
Description=Docker Application Container Engine
After=network-online.target containerd.service squid.service
Wants=network-online.target containerd.service squid.service

[Service]
Type=notify
Environment=HTTP_PROXY=http://127.0.0.1:3128
Environment=HTTPS_PROXY=http://127.0.0.1:3128
Environment=NO_PROXY=localhost,127.0.0.1
ExecStart=/usr/local/bin/dockerd --host=unix:///run/docker.sock --containerd=/run/containerd/containerd.sock --group=docker
ExecReload=/bin/kill -s HUP $MAINPID
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
UNIT

cat >/etc/squid/squid.conf <<'SQUID'
http_port 0.0.0.0:3128
acl local_runner src 127.0.0.1/32 172.17.0.0/16 172.18.0.0/16
acl ssl_ports port 443
acl connect method CONNECT
acl github_results dstdom_regex -i ^productionresultssa[0-9]+[.]blob[.]core[.]windows[.]net$
acl approved_domains dstdomain .github.com .githubusercontent.com .actions.githubusercontent.com .ghcr.io .sigstore.dev .docker.io .docker.com .pypi.org .pythonhosted.org mirror.gcr.io dl-cdn.alpinelinux.org
http_access allow local_runner connect ssl_ports github_results
http_access allow local_runner connect ssl_ports approved_domains
http_access deny all
cache deny all
access_log stdio:/var/log/squid/access.log
cache_log /var/log/squid/cache.log
request_header_access Proxy-Authorization deny all
forwarded_for delete
via off
SQUID

systemctl daemon-reload
squid -k parse
systemctl enable squid.service containerd.service docker.service
systemctl restart squid.service
systemctl restart containerd.service docker.service
