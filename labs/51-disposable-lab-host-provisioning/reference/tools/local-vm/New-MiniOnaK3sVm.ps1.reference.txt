[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath,

    [Parameter(Mandatory = $true)]
    [string]$VmDirectory,

    [Parameter(Mandatory = $true)]
    [string]$PublicKeyPath,

    [Parameter(Mandatory = $true)]
    [string]$KataValuesPath,

    [string]$VmName = "snsd-mini-ona-k3s",
    [int]$MemoryMb = 8192,
    [int]$ProcessorCount = 4,
    [string]$DiskSize = "60GB",
    [switch]$Start
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ubuntu 24.04 release-20260826 VMware VMDK. The date-specific source is:
# https://cloud-images.ubuntu.com/releases/noble/release-20260826/
$expectedImageSha256 = "fb3ba097a9013d759fa13ab22d2b4118bd55452c617ca3758a55303eea96de6e"
$helmVersion = "v4.2.3"
$helmSha256 = "e9b88b4ee95b18c706839c28d3a0220e5bc470e9cd9262410c90793c45ff8b7c"
$kataVersion = "4.0.0"
$kataChartSha256 = "68ee406af84761d85ddd6942bd3f0b11ba4f19ce19bf46ec2a4ea29f93926a4b"
$vmwareRoot = "C:\Program Files (x86)\VMware\VMware Workstation"
$diskManager = Join-Path $vmwareRoot "vmware-vdiskmanager.exe"
$vmRun = Join-Path $vmwareRoot "vmrun.exe"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

if ($VmName -notmatch '^[a-z0-9][a-z0-9-]{2,31}$') {
    throw "VmName must be a bounded lowercase DNS label."
}
if (-not (Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
    throw "Reviewed Ubuntu VMware image is missing: $ImagePath"
}
if (-not (Test-Path -LiteralPath $PublicKeyPath -PathType Leaf)) {
    throw "Public SSH key is missing: $PublicKeyPath"
}
if (-not (Test-Path -LiteralPath $KataValuesPath -PathType Leaf)) {
    throw "Reviewed Kata values file is missing: $KataValuesPath"
}
foreach ($tool in @($diskManager, $vmRun)) {
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
        throw "Required VMware tool is missing: $tool"
    }
}
if ($MemoryMb -lt 6144 -or $MemoryMb -gt 12288) {
    throw "MemoryMb must remain between 6144 and 12288."
}
if ($ProcessorCount -lt 2 -or $ProcessorCount -gt 6) {
    throw "ProcessorCount must remain between 2 and 6."
}
if ($DiskSize -notmatch '^(5[0-9]|6[0-9]|7[0-9]|80)GB$') {
    throw "DiskSize must remain between 50GB and 80GB."
}

$resolvedImage = (Resolve-Path -LiteralPath $ImagePath).Path
$actualImageSha256 = (Get-FileHash -LiteralPath $resolvedImage -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualImageSha256 -ne $expectedImageSha256) {
    throw "Reviewed Ubuntu image checksum mismatch: $actualImageSha256"
}

$resolvedVmDirectory = [System.IO.Path]::GetFullPath($VmDirectory)
if (Test-Path -LiteralPath $resolvedVmDirectory) {
    throw "VM target already exists; refusing to overwrite: $resolvedVmDirectory"
}
$vmParent = Split-Path -Parent $resolvedVmDirectory
New-Item -ItemType Directory -Path $vmParent -Force | Out-Null
New-Item -ItemType Directory -Path $resolvedVmDirectory | Out-Null

$publicKey = (Get-Content -LiteralPath $PublicKeyPath -Raw).Trim()
if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+ [A-Za-z0-9@._-]+$') {
    throw "The reviewed public key must be a single ED25519 public key."
}
$kataValues = (Get-Content -LiteralPath $KataValuesPath -Raw).TrimEnd()
$requiredKataValues = @(
    "deploymentMode: job",
    "k8sDistribution: k3s",
    "disableAll: true",
    "qemu-runtime-rs:",
    "enabled: true",
    "node-feature-discovery:"
)
foreach ($requiredValue in $requiredKataValues) {
    if (-not $kataValues.Contains($requiredValue)) {
        throw "Kata values file is missing required reviewed content: $requiredValue"
    }
}
if ($kataValues -match "`t") {
    throw "Kata values file must not contain tab indentation."
}
$kataValuesIndented = (($kataValues -split "`r?`n") | ForEach-Object { "      $_" }) -join "`n"
$kataValuesSha256 = (Get-FileHash -LiteralPath $KataValuesPath -Algorithm SHA256).Hash.ToLowerInvariant()

$diskPath = Join-Path $resolvedVmDirectory "$VmName.vmdk"
$vmxPath = Join-Path $resolvedVmDirectory "$VmName.vmx"

try {
    & $diskManager -r $resolvedImage -t 0 $diskPath
    if ($LASTEXITCODE -ne 0) {
        throw "VMware disk conversion failed with exit code $LASTEXITCODE"
    }
    & $diskManager -x $DiskSize $diskPath
    if ($LASTEXITCODE -ne 0) {
        throw "VMware disk expansion failed with exit code $LASTEXITCODE"
    }

    $metadata = @"
instance-id: snsd-mini-ona-k3s-001
local-hostname: $VmName
network:
  version: 2
  ethernets:
    enp2s0:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 100
    enp11s0:
      dhcp4: true
      dhcp4-overrides:
        use-routes: false
"@

    $userData = @"
#cloud-config
hostname: $VmName
manage_etc_hosts: true
disable_root: true
ssh_pwauth: false
users:
  - name: miniona
    gecos: Mini Ona Runtime Operator
    groups: [adm, users]
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - $publicKey
growpart:
  mode: auto
  devices: ['/']
resize_rootfs: true
package_update: true
package_upgrade: false
packages:
  - ca-certificates
  - conntrack
  - cpu-checker
  - curl
  - git
  - jq
  - openssh-server
  - open-vm-tools
  - python3
  - qemu-system-x86
  - redis-server
  - socat
  - ufw
  - zstd
write_files:
  - path: /etc/sudoers.d/60-mini-ona-runtime-status
    owner: root:root
    permissions: '0440'
    content: |
      miniona ALL=(root) NOPASSWD: /usr/local/sbin/mini-ona-runtime-status
      miniona ALL=(root) NOPASSWD: /usr/local/sbin/mini-ona-kata-live-validator
  - path: /etc/ssh/sshd_config.d/60-mini-ona-runtime.conf
    owner: root:root
    permissions: '0644'
    content: |
      PasswordAuthentication no
      KbdInteractiveAuthentication no
      PermitRootLogin no
      AllowUsers miniona
  - path: /etc/modules-load.d/mini-ona-kvm.conf
    owner: root:root
    permissions: '0644'
    content: |
      kvm
  - path: /etc/rancher/k3s/config.yaml
    owner: root:root
    permissions: '0600'
    content: |
      write-kubeconfig-mode: "0600"
      secrets-encryption: true
      disable:
        - traefik
        - servicelb
      flannel-backend: vxlan
      node-label:
        - "zero-trust.snsd.local/managed=true"
        - "platform.snsd/role=mini-ona-runtime"
  - path: /etc/systemd/system/k3s.service
    owner: root:root
    permissions: '0644'
    content: |
      [Unit]
      Description=Lightweight Kubernetes
      Wants=network-online.target
      After=network-online.target

      [Service]
      Type=notify
      Environment=K3S_KUBECONFIG_MODE=600
      ExecStart=/usr/local/bin/k3s server --config /etc/rancher/k3s/config.yaml
      KillMode=process
      Delegate=yes
      LimitNOFILE=1048576
      LimitNPROC=infinity
      LimitCORE=infinity
      TasksMax=infinity
      TimeoutStartSec=0
      Restart=always
      RestartSec=5s

      [Install]
      WantedBy=multi-user.target
  - path: /etc/mini-ona/kata-deploy-values.yaml
    owner: root:root
    permissions: '0600'
    content: |
$kataValuesIndented
  - path: /usr/local/sbin/mini-ona-runtime-status
    owner: root:root
    permissions: '0755'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      echo 'cloud-init:'
      cloud-init status --format json | jq '{status,errors,recoverable_errors}'
      echo 'k3s:'
      /usr/local/bin/k3s --version | head -n 1
      /usr/local/bin/k3s kubectl get --raw=/readyz
      /usr/local/bin/k3s kubectl get nodes -o custom-columns=NAME:.metadata.name,READY:.status.conditions[-1].status,KATA:.metadata.labels.katacontainers\\.io/kata-runtime --no-headers
      echo 'runtime-class:'
      /usr/local/bin/k3s kubectl get runtimeclass kata-qemu-runtime-rs -o custom-columns=NAME:.metadata.name,HANDLER:.handler --no-headers
      echo 'redis:'
      redis-cli --no-auth-warning ping
      redis-cli --no-auth-warning config get bind | tail -n 1
      redis-cli --no-auth-warning config get protected-mode | tail -n 1
      systemctl is-active redis-server
      echo 'kvm:'
      test -c /dev/kvm
      echo present
      echo 'failed-units:'
      systemctl --failed --no-legend --plain || true
      echo 'firewall:'
      ufw status verbose
  - path: /usr/local/sbin/mini-ona-kata-live-validator
    owner: root:root
    permissions: '0755'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      test "`$#" -eq 0
      k3s=/usr/local/bin/k3s
      namespace=mini-ona-kata-validation
      policy=mini-ona-kata-validation-runtime
      binding=mini-ona-kata-validation-runtime
      image='docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f'
      phase=initialization

      cleanup() {
        "`$k3s" kubectl delete namespace "`$namespace" --ignore-not-found --wait=true --timeout=180s >/dev/null 2>&1 || true
        "`$k3s" kubectl delete validatingadmissionpolicybinding "`$binding" --ignore-not-found >/dev/null 2>&1 || true
        "`$k3s" kubectl delete validatingadmissionpolicy "`$policy" --ignore-not-found >/dev/null 2>&1 || true
      }
      wait_for_log_line() {
        pod="`$1"
        expected="`$2"
        for _ in {1..30}; do
          if "`$k3s" kubectl logs -n "`$namespace" "`$pod" 2>/dev/null | grep -Fqx -- "`$expected"; then
            return 0
          fi
          sleep 1
        done
        return 1
      }
      fail_sanitized() {
        rc="`$?"
        trap - ERR EXIT
        cleanup
        printf '{"schema_version":"1.0.0","scope":"MINI_ONA_KATA_LIVE_VALIDATION","result":"FAILED","phase":"%s","exit_code":%s,"rollback_cleanup":true,"raw_runtime_output_stored":false}\n' "`$phase" "`$rc"
        exit "`$rc"
      }
      trap fail_sanitized ERR
      trap cleanup EXIT
      cleanup

      phase=baseline_apply
      "`$k3s" kubectl apply -f - >/dev/null <<'VALIDATION_BASELINE'
      apiVersion: admissionregistration.k8s.io/v1
      kind: ValidatingAdmissionPolicy
      metadata:
        name: mini-ona-kata-validation-runtime
      spec:
        failurePolicy: Fail
        matchConstraints:
          resourceRules:
            - apiGroups: [""]
              apiVersions: ["v1"]
              operations: ["CREATE", "UPDATE"]
              resources: ["pods"]
        validations:
          - expression: "object.spec.runtimeClassName == 'kata-qemu-runtime-rs'"
            message: "Mini-Ona validation pods require the approved Kata runtime"
      ---
      apiVersion: admissionregistration.k8s.io/v1
      kind: ValidatingAdmissionPolicyBinding
      metadata:
        name: mini-ona-kata-validation-runtime
      spec:
        policyName: mini-ona-kata-validation-runtime
        validationActions: [Deny]
        matchResources:
          namespaceSelector:
            matchLabels:
              platform.snsd/mini-ona-validation: "true"
      ---
      apiVersion: v1
      kind: Namespace
      metadata:
        name: mini-ona-kata-validation
        labels:
          platform.snsd/mini-ona-validation: "true"
          pod-security.kubernetes.io/enforce: restricted
          pod-security.kubernetes.io/enforce-version: v1.36
      ---
      apiVersion: v1
      kind: ResourceQuota
      metadata:
        name: validation-quota
        namespace: mini-ona-kata-validation
      spec:
        hard:
          pods: "2"
          requests.cpu: "1"
          requests.memory: 1Gi
          limits.cpu: "2"
          limits.memory: 2Gi
      ---
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      metadata:
        name: default-deny
        namespace: mini-ona-kata-validation
      spec:
        podSelector: {}
        policyTypes: [Ingress, Egress]
      ---
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: sanitized-checkpoint
        namespace: mini-ona-kata-validation
      data:
        digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      VALIDATION_BASELINE

      phase=bypass_default_runtime
      if "`$k3s" kubectl apply -f - >/dev/null 2>&1 <<'BYPASS_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: bypass-default-runtime
        namespace: mini-ona-kata-validation
      spec:
        containers:
          - name: bypass
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "true"]
            securityContext:
              allowPrivilegeEscalation: false
              capabilities: {drop: ["ALL"]}
              runAsNonRoot: true
              runAsUser: 65532
              seccompProfile: {type: RuntimeDefault}
        restartPolicy: Never
      BYPASS_POD
      then
        false
      fi

      phase=negative_privilege
      if "`$k3s" kubectl apply -f - >/dev/null 2>&1 <<'PRIVILEGED_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: privileged-bypass
        namespace: mini-ona-kata-validation
      spec:
        runtimeClassName: kata-qemu-runtime-rs
        containers:
          - name: bypass
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "true"]
            securityContext: {privileged: true}
        restartPolicy: Never
      PRIVILEGED_POD
      then
        false
      fi

      phase=positive_apply
      "`$k3s" kubectl apply -f - >/dev/null <<'POSITIVE_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: positive
        namespace: mini-ona-kata-validation
      spec:
        runtimeClassName: kata-qemu-runtime-rs
        automountServiceAccountToken: false
        securityContext:
          runAsNonRoot: true
          runAsUser: 65532
          runAsGroup: 65532
          seccompProfile: {type: RuntimeDefault}
        containers:
          - name: validation
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "cat /checkpoint/digest; printf '\nKATA_POSITIVE\n'; sleep 45"]
            resources:
              requests: {cpu: 50m, memory: 32Mi}
              limits: {cpu: 250m, memory: 128Mi}
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities: {drop: ["ALL"]}
            volumeMounts:
              - {name: checkpoint, mountPath: /checkpoint, readOnly: true}
              - {name: tmp, mountPath: /tmp}
        volumes:
          - name: checkpoint
            configMap: {name: sanitized-checkpoint}
          - name: tmp
            emptyDir: {sizeLimit: 16Mi}
        restartPolicy: Never
      POSITIVE_POD
      phase=positive_ready
      "`$k3s" kubectl wait --for=condition=Ready pod/positive -n "`$namespace" --timeout=240s >/dev/null
      phase=positive_log
      wait_for_log_line positive KATA_POSITIVE
      phase=positive_runtime_class
      "`$k3s" kubectl get pod positive -n "`$namespace" -o jsonpath='{.spec.runtimeClassName}' | grep -qx kata-qemu-runtime-rs
      phase=positive_vm_process
      pgrep -f 'qemu-system|cloud-hypervisor' >/dev/null
      phase=positive_cleanup
      "`$k3s" kubectl delete pod positive -n "`$namespace" --wait=true --timeout=120s >/dev/null

      phase=persistence_apply
      "`$k3s" kubectl apply -f - >/dev/null <<'PERSISTENCE_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: persistence
        namespace: mini-ona-kata-validation
      spec:
        runtimeClassName: kata-qemu-runtime-rs
        automountServiceAccountToken: false
        securityContext:
          runAsNonRoot: true
          runAsUser: 65532
          runAsGroup: 65532
          seccompProfile: {type: RuntimeDefault}
        containers:
          - name: validation
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "cat /checkpoint/digest"]
            resources:
              requests: {cpu: 50m, memory: 32Mi}
              limits: {cpu: 250m, memory: 128Mi}
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities: {drop: ["ALL"]}
            volumeMounts:
              - {name: checkpoint, mountPath: /checkpoint, readOnly: true}
              - {name: tmp, mountPath: /tmp}
        volumes:
          - name: checkpoint
            configMap: {name: sanitized-checkpoint}
          - name: tmp
            emptyDir: {sizeLimit: 16Mi}
        restartPolicy: Never
      PERSISTENCE_POD
      phase=persistence_complete
      "`$k3s" kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/persistence -n "`$namespace" --timeout=240s >/dev/null
      phase=persistence_log
      wait_for_log_line persistence 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

      phase=egress_apply
      "`$k3s" kubectl apply -f - >/dev/null <<'EGRESS_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: egress-denial
        namespace: mini-ona-kata-validation
      spec:
        runtimeClassName: kata-qemu-runtime-rs
        automountServiceAccountToken: false
        securityContext:
          runAsNonRoot: true
          runAsUser: 65532
          runAsGroup: 65532
          seccompProfile: {type: RuntimeDefault}
        containers:
          - name: validation
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "if wget -T 4 -q -O /dev/null http://1.1.1.1; then exit 41; else echo EGRESS_BLOCKED; fi"]
            resources:
              requests: {cpu: 50m, memory: 32Mi}
              limits: {cpu: 250m, memory: 128Mi}
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities: {drop: ["ALL"]}
            volumeMounts:
              - {name: tmp, mountPath: /tmp}
        volumes:
          - name: tmp
            emptyDir: {sizeLimit: 16Mi}
        restartPolicy: Never
      EGRESS_POD
      phase=egress_complete
      "`$k3s" kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/egress-denial -n "`$namespace" --timeout=240s >/dev/null
      phase=egress_log
      wait_for_log_line egress-denial EGRESS_BLOCKED

      phase=deadline_apply
      "`$k3s" kubectl apply -f - >/dev/null <<'DEADLINE_POD'
      apiVersion: v1
      kind: Pod
      metadata:
        name: deadline
        namespace: mini-ona-kata-validation
      spec:
        runtimeClassName: kata-qemu-runtime-rs
        activeDeadlineSeconds: 5
        automountServiceAccountToken: false
        securityContext:
          runAsNonRoot: true
          runAsUser: 65532
          runAsGroup: 65532
          seccompProfile: {type: RuntimeDefault}
        containers:
          - name: validation
            image: docker.io/library/busybox@sha256:b7f3d86d6e84fc17718c48bcde1450807faa2d56704205c697b4bd5df7b9e29f
            command: ["sh", "-c", "sleep 60"]
            resources:
              requests: {cpu: 50m, memory: 32Mi}
              limits: {cpu: 250m, memory: 128Mi}
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities: {drop: ["ALL"]}
            volumeMounts:
              - {name: tmp, mountPath: /tmp}
        volumes:
          - name: tmp
            emptyDir: {sizeLimit: 16Mi}
        restartPolicy: Never
      DEADLINE_POD
      phase=deadline_failed
      "`$k3s" kubectl wait --for=jsonpath='{.status.phase}'=Failed pod/deadline -n "`$namespace" --timeout=240s >/dev/null
      phase=deadline_reason
      "`$k3s" kubectl get pod deadline -n "`$namespace" -o jsonpath='{.status.reason}' | grep -qx DeadlineExceeded

      phase=rollback_cleanup
      cleanup
      trap - EXIT
      phase=rollback_verify_namespace
      if "`$k3s" kubectl get namespace "`$namespace" >/dev/null 2>&1; then exit 51; fi
      phase=rollback_verify_policy
      if "`$k3s" kubectl get validatingadmissionpolicy "`$policy" >/dev/null 2>&1; then exit 52; fi
      printf '%s\n' '{"schema_version":"1.0.0","scope":"MINI_ONA_KATA_LIVE_VALIDATION","runtime_class":"kata-qemu-runtime-rs","positive":true,"negative_privilege":true,"bypass_default_runtime":true,"egress_direct_ip_denied":true,"persistence_recreate":true,"deadline_enforced":true,"sandbox_vm_process":true,"rollback_cleanup":true,"raw_runtime_output_stored":false}'
  - path: /usr/local/sbin/bootstrap-mini-ona-k3s
    owner: root:root
    permissions: '0700'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      install -d -o root -g root -m 0700 /var/lib/rancher/k3s/agent/images
      curl --fail --location --retry 3 --output /tmp/k3s https://github.com/k3s-io/k3s/releases/download/v1.36.3%2Bk3s1/k3s
      echo '2f98a9f8fe5782479ee2d54e70a1b10a7f6fd4cae8d38ed3098452dc6eed76b5  /tmp/k3s' | sha256sum --check --strict
      install -o root -g root -m 0755 /tmp/k3s /usr/local/bin/k3s
      curl --fail --location --retry 3 --output /tmp/k3s-airgap-images-amd64.tar.zst https://github.com/k3s-io/k3s/releases/download/v1.36.3%2Bk3s1/k3s-airgap-images-amd64.tar.zst
      echo 'a197d79e979cc3f4fa9bca8f500bd70092b25c1b5ebda68b35a25f792abd42b0  /tmp/k3s-airgap-images-amd64.tar.zst' | sha256sum --check --strict
      install -o root -g root -m 0600 /tmp/k3s-airgap-images-amd64.tar.zst /var/lib/rancher/k3s/agent/images/k3s-airgap-images-amd64.tar.zst
      rm -f /tmp/k3s /tmp/k3s-airgap-images-amd64.tar.zst
      curl --fail --location --retry 3 --output /tmp/helm-$helmVersion-linux-amd64.tar.gz https://get.helm.sh/helm-$helmVersion-linux-amd64.tar.gz
      echo '$helmSha256  /tmp/helm-$helmVersion-linux-amd64.tar.gz' | sha256sum --check --strict
      tar -xzf /tmp/helm-$helmVersion-linux-amd64.tar.gz -C /tmp
      install -o root -g root -m 0755 /tmp/linux-amd64/helm /usr/local/bin/helm
      rm -rf /tmp/linux-amd64 /tmp/helm-$helmVersion-linux-amd64.tar.gz
      curl --fail --location --retry 3 --output /tmp/kata-deploy-$kataVersion.tgz https://github.com/kata-containers/kata-containers/releases/download/$kataVersion/kata-deploy-$kataVersion.tgz
      echo '$kataChartSha256  /tmp/kata-deploy-$kataVersion.tgz' | sha256sum --check --strict
      systemctl daemon-reload
      systemctl enable --now k3s
      for attempt in {1..60}; do
        if /usr/local/bin/k3s kubectl get --raw=/readyz 2>/dev/null | grep -qx ok; then
          break
        fi
        sleep 2
      done
      /usr/local/bin/k3s kubectl get --raw=/readyz | grep -qx ok
      /usr/local/bin/helm upgrade --install kata-deploy /tmp/kata-deploy-$kataVersion.tgz --namespace kube-system --kubeconfig /etc/rancher/k3s/k3s.yaml --values /etc/mini-ona/kata-deploy-values.yaml --wait --wait-for-jobs --timeout 30m
      rm -f /tmp/kata-deploy-$kataVersion.tgz
      /usr/local/bin/k3s kubectl get runtimeclass kata-qemu-runtime-rs -o jsonpath='{.handler}' | grep -qx kata-qemu-runtime-rs
      /usr/local/bin/k3s kubectl get nodes -l katacontainers.io/kata-runtime=true --no-headers | grep -q .
      redis-cli --no-auth-warning config get bind | tail -n 1 | grep -qx '127.0.0.1 -::1'
      redis-cli --no-auth-warning config get protected-mode | tail -n 1 | grep -qx yes
      touch /var/lib/mini-ona-k3s-ready
runcmd:
  - [systemctl, restart, ssh]
  - [ufw, default, deny, incoming]
  - [ufw, default, allow, outgoing]
  - [ufw, allow, from, 192.168.8.0/24, to, any, port, '22', proto, tcp]
  - [ufw, allow, from, 192.168.1.0/24, to, any, port, '22', proto, tcp]
  - [ufw, --force, enable]
  - [/usr/local/sbin/bootstrap-mini-ona-k3s]
  - [touch, /var/lib/mini-ona-vm-ready]
final_message: SNSD Mini-Ona k3s runtime VM initialization complete
"@

    $metadataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($metadata))
    $userDataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($userData))
    $vmx = @"
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "21"
displayName = "$VmName"
annotation = "Bounded non-production Mini-Ona k3s runtime; NAT and host-only only"
guestOS = "ubuntu-64"
firmware = "efi"
uefi.secureBoot.enabled = "TRUE"
numvcpus = "$ProcessorCount"
cpuid.coresPerSocket = "$ProcessorCount"
memsize = "$MemoryMb"
mem.hotadd = "FALSE"
vhv.enable = "TRUE"
hypervisor.cpuid.v0 = "FALSE"
vpmc.enable = "TRUE"
tools.syncTime = "TRUE"
tools.upgrade.policy = "manual"
sound.present = "FALSE"
usb.present = "FALSE"
sharedFolder.maxNum = "0"
isolation.tools.copy.disable = "TRUE"
isolation.tools.paste.disable = "TRUE"
isolation.tools.dnd.disable = "TRUE"
isolation.tools.hgfs.disable = "TRUE"
pciBridge0.present = "TRUE"
pciBridge4.present = "TRUE"
pciBridge4.virtualDev = "pcieRootPort"
pciBridge4.functions = "8"
pciBridge4.pciSlotNumber = "17"
pciBridge5.present = "TRUE"
pciBridge5.virtualDev = "pcieRootPort"
pciBridge5.functions = "8"
pciBridge5.pciSlotNumber = "21"
pciBridge6.present = "TRUE"
pciBridge6.virtualDev = "pcieRootPort"
pciBridge6.functions = "8"
pciBridge6.pciSlotNumber = "22"
pciBridge7.present = "TRUE"
pciBridge7.virtualDev = "pcieRootPort"
pciBridge7.functions = "8"
pciBridge7.pciSlotNumber = "23"
scsi0.present = "TRUE"
scsi0.virtualDev = "lsilogic"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "$VmName.vmdk"
ethernet0.present = "TRUE"
ethernet0.connectionType = "nat"
ethernet0.virtualDev = "vmxnet3"
ethernet0.startConnected = "TRUE"
ethernet0.addressType = "generated"
ethernet1.present = "TRUE"
ethernet1.connectionType = "custom"
ethernet1.vnet = "VMnet1"
ethernet1.virtualDev = "vmxnet3"
ethernet1.startConnected = "TRUE"
ethernet1.addressType = "generated"
floppy0.present = "FALSE"
guestinfo.metadata = "$metadataBase64"
guestinfo.metadata.encoding = "base64"
guestinfo.userdata = "$userDataBase64"
guestinfo.userdata.encoding = "base64"
"@
    [System.IO.File]::WriteAllText($vmxPath, $vmx, $utf8NoBom)

    if ($Start) {
        & $vmRun -T ws start $vmxPath nogui
        if ($LASTEXITCODE -ne 0) {
            throw "VMware VM start failed with exit code $LASTEXITCODE"
        }
    }
}
catch {
    if (-not (Test-Path -LiteralPath $vmxPath -PathType Leaf)) {
        Remove-Item -LiteralPath $resolvedVmDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
    throw
}

[pscustomobject]@{
    vm_name = $VmName
    vmx_path = $vmxPath
    image_release = "20260826"
    image_sha256 = $actualImageSha256
    kata_values_sha256 = $kataValuesSha256
    helm_version = $helmVersion
    kata_version = $kataVersion
    processors = $ProcessorCount
    memory_mb = $MemoryMb
    disk_size = $DiskSize
    nested_virtualization = $true
    network = @("VMnet8_NAT", "VMnet1_HOST_ONLY")
    password_authentication = $false
    root_ssh = $false
    shared_folders = $false
    started = [bool]$Start
} | ConvertTo-Json -Depth 4
