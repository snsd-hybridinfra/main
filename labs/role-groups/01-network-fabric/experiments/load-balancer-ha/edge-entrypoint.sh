#!/bin/sh
set -eu

if ! id lab >/dev/null 2>&1; then
  adduser -D -s /bin/sh lab
  temp_password="$(head -c 32 /dev/urandom | base64)"
  echo "lab:$temp_password" | chpasswd
  unset temp_password
fi

mkdir -p /home/lab/.ssh /run/sshd /run/nginx
chown -R lab:lab /home/lab/.ssh
chmod 700 /home/lab/.ssh
ssh-keygen -A

cat > /etc/ssh/sshd_config <<'EOF'
Port 22
ListenAddress 172.31.10.10
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
AllowUsers lab
UsePAM no
PrintMotd no
Subsystem sftp internal-sftp
EOF

nginx -t
/usr/sbin/sshd -e
exec nginx -g 'daemon off;'
