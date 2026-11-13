#!/bin/sh
set -eu

: "${IOSXE_MOCK_USER:?IOSXE_MOCK_USER is required}"
: "${IOSXE_MOCK_PASSWORD:?IOSXE_MOCK_PASSWORD is required}"

if ! id "$IOSXE_MOCK_USER" >/dev/null 2>&1; then
  adduser -D -s /usr/local/bin/mock-cli "$IOSXE_MOCK_USER"
fi
echo "$IOSXE_MOCK_USER:$IOSXE_MOCK_PASSWORD" | chpasswd

mkdir -p /run/mock /run/sshd
ssh-keygen -A
openssl req -x509 -newkey rsa:2048 -nodes   -keyout /run/mock/device.key   -out /run/mock/device.crt   -days 1   -subj "/CN=device" >/dev/null 2>&1

cat > /etc/ssh/sshd_config <<'EOF'
Port 22
ListenAddress 0.0.0.0
PermitRootLogin no
PasswordAuthentication yes
KbdInteractiveAuthentication no
PubkeyAuthentication no
AllowUsers iosxe
PrintMotd no
EOF

python3 /opt/mock/device_server.py &
exec /usr/sbin/sshd -D -e
