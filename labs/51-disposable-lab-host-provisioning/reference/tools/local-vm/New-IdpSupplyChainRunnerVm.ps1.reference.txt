[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath,

    [Parameter(Mandatory = $true)]
    [string]$VmDirectory,

    [Parameter(Mandatory = $true)]
    [string]$DispatchPublicKeyPath,

    [Parameter(Mandatory = $true)]
    [string]$RunnerBundleManifestPath,

    [Parameter(Mandatory = $true)]
    [string]$RunnerBundlePath,

    [string]$VmName = "snsd-idp-supply-chain-runner",
    [int]$MemoryMb = 8192,
    [int]$ProcessorCount = 4,
    [string]$DiskSize = "80GB",
    [switch]$Start
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ubuntu 24.04 release-20260826 VMware VMDK. A different base image requires a
# separately reviewed provisioner change; the digest is intentionally not input.
$expectedImageSha256 = "fb3ba097a9013d759fa13ab22d2b4118bd55452c617ca3758a55303eea96de6e"
$vmwareRoot = "C:\Program Files (x86)\VMware\VMware Workstation"
$diskManager = Join-Path $vmwareRoot "vmware-vdiskmanager.exe"
$vmRun = Join-Path $vmwareRoot "vmrun.exe"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

if ($VmName -notmatch '^[a-z0-9][a-z0-9-]{2,47}$') {
    throw "VmName must be a bounded lowercase DNS label."
}
foreach ($path in @($ImagePath, $DispatchPublicKeyPath, $RunnerBundleManifestPath, $RunnerBundlePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required reviewed input is missing: $path"
    }
}
foreach ($tool in @($diskManager, $vmRun)) {
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
        throw "Required VMware tool is missing: $tool"
    }
}
if ($MemoryMb -lt 6144 -or $MemoryMb -gt 16384) {
    throw "MemoryMb must remain between 6144 and 16384."
}
if ($ProcessorCount -lt 2 -or $ProcessorCount -gt 8) {
    throw "ProcessorCount must remain between 2 and 8."
}
if ($DiskSize -notmatch '^(6[0-9]|7[0-9]|8[0-9]|9[0-9]|100)GB$') {
    throw "DiskSize must remain between 60GB and 100GB."
}

$resolvedImage = (Resolve-Path -LiteralPath $ImagePath).Path
$actualImageSha256 = (Get-FileHash -LiteralPath $resolvedImage -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualImageSha256 -ne $expectedImageSha256) {
    throw "Reviewed Ubuntu image checksum mismatch: $actualImageSha256"
}

$publicKey = (Get-Content -LiteralPath $DispatchPublicKeyPath -Raw).Trim()
if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+(?: [A-Za-z0-9@._-]+)?$') {
    throw "The dispatch key must be a single ED25519 public key."
}
$restrictedPublicKey = 'restrict,command="/usr/local/sbin/idp-runner-dispatch" ' + $publicKey

$manifest = Get-Content -LiteralPath $RunnerBundleManifestPath -Raw | ConvertFrom-Json
if ($manifest.schema_version -ne "1.0.0" -or $manifest.os -ne "ubuntu-24.04" -or $manifest.architecture -ne "x86_64") {
    throw "Runner bundle manifest platform is not exact."
}
$bundleUri = [Uri]$manifest.bundle.url
if ($bundleUri.Scheme -ne "https" -or $bundleUri.DnsSafeHost -ne $manifest.bundle.approved_host) {
    throw "Runner bundle URL must use HTTPS on its reviewed host."
}
if ($manifest.bundle.sha256 -notmatch '^[0-9a-f]{64}$') {
    throw "Runner bundle SHA-256 is invalid."
}
$resolvedBundle = (Resolve-Path -LiteralPath $RunnerBundlePath).Path
$actualBundleSha256 = (Get-FileHash -LiteralPath $resolvedBundle -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualBundleSha256 -ne $manifest.bundle.sha256) {
    throw "Runner bundle checksum differs from its reviewed manifest."
}
$bundleAssetName = [IO.Path]::GetFileName(([Uri]$manifest.bundle.url).AbsolutePath)
if ([IO.Path]::GetFileName($resolvedBundle) -ne $bundleAssetName) {
    throw "Runner bundle filename differs from its release authority."
}
$resolvedManifest = (Resolve-Path -LiteralPath $RunnerBundleManifestPath).Path
$bundleSourceDirectory = Split-Path -Parent $resolvedBundle
if ((Split-Path -Parent $resolvedManifest) -ne $bundleSourceDirectory) {
    throw "Runner bundle and manifest must share one isolated ISO source directory."
}
$isoSourceFiles = @(Get-ChildItem -LiteralPath $bundleSourceDirectory -File)
if ($isoSourceFiles.Count -ne 2 -or $isoSourceFiles.Name -notcontains $bundleAssetName -or $isoSourceFiles.Name -notcontains "runner-bundle-manifest.json") {
    throw "Runner bundle ISO source directory must contain only the bundle and manifest."
}
if ($manifest.bundle.version -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$') {
    throw "Runner bundle version is invalid."
}

$expectedTools = @("actions-runner", "cosign", "docker", "docker-buildx", "gh", "git", "syft", "trivy")
$expectedPaths = @{
    "actions-runner" = "/opt/actions-runner/bin/Runner.Listener"
    "cosign" = "/usr/local/bin/cosign"
    "docker" = "/usr/local/bin/docker"
    "docker-buildx" = "/usr/local/lib/docker/cli-plugins/docker-buildx"
    "gh" = "/usr/local/bin/gh"
    "git" = "/usr/local/bin/git"
    "syft" = "/usr/local/bin/syft"
    "trivy" = "/usr/local/bin/trivy"
}
# The protected workflow variable IDP_TOOL_DOCKER_BUILDX_SHA256 must equal the
# reviewed docker-buildx entry below before a publish job can start.
$actualTools = @($manifest.tools.PSObject.Properties.Name | Sort-Object)
if (@(Compare-Object -ReferenceObject $expectedTools -DifferenceObject $actualTools -SyncWindow 0).Count -ne 0) {
    throw "Runner bundle tool set is not exact."
}
foreach ($name in $expectedTools) {
    $record = $manifest.tools.$name
    if ($record.path -ne $expectedPaths[$name] -or $record.sha256 -notmatch '^[0-9a-f]{64}$' -or $record.version -notmatch '^[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}$') {
        throw "Runner bundle tool authority is invalid: $name"
    }
}

$resolvedVmDirectory = [System.IO.Path]::GetFullPath($VmDirectory)
if (Test-Path -LiteralPath $resolvedVmDirectory) {
    throw "VM target already exists; refusing to overwrite: $resolvedVmDirectory"
}
$vmParent = Split-Path -Parent $resolvedVmDirectory
if (-not $vmParent) {
    throw "VM target must have an explicit parent directory."
}

$manifestJson = $manifest | ConvertTo-Json -Depth 10 -Compress
$manifestBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($manifestJson))
$userDataTemplate = @'
#cloud-config
hostname: __VM_NAME__
manage_etc_hosts: true
disable_root: true
ssh_pwauth: false
users:
  - name: idprunner
    gecos: Ephemeral IDP Supply Chain Runner
    groups: [users]
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - __RESTRICTED_PUBLIC_KEY__
growpart:
  mode: auto
  devices: ['/']
resize_rootfs: true
package_update: true
package_upgrade: false
packages:
  - ca-certificates
  - curl
  - openssh-server
  - open-vm-tools
  - python3
  - 'git=1:2.43.0-1ubuntu7.3'
  - squid
  - tar
  - ufw
write_files:
  - path: /etc/idp-supply-chain/runner-bundle-manifest.json
    owner: root:root
    permissions: '0444'
    encoding: b64
    content: __MANIFEST_BASE64__
  - path: /etc/ssh/sshd_config.d/70-idp-supply-chain-runner.conf
    owner: root:root
    permissions: '0644'
    content: |
      PasswordAuthentication no
      KbdInteractiveAuthentication no
      PermitRootLogin no
      AllowAgentForwarding no
      AllowTcpForwarding no
      X11Forwarding no
      PermitTunnel no
      AllowUsers idprunner
  - path: /usr/local/sbin/idp-runner-dispatch
    owner: root:root
    permissions: '0755'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      if [[ "${SSH_ORIGINAL_COMMAND:-}" == "proxy-denials" ]]; then
        tail -n 200 /var/log/squid/access.log |
          awk '$4 ~ /DENIED/ {print "client=" $3 " result=" $4 " method=" $6 " target=" $7}'
        exit 0
      fi
      if [[ -n "${SSH_ORIGINAL_COMMAND:-}" ]]; then
        echo "remote commands are denied" >&2
        exit 64
      fi
      [[ -f /var/lib/idp-supply-chain-runner-ready ]] || exit 69
      exec 9>/run/lock/idp-supply-chain-runner.lock
      flock -n 9 || exit 75
      IFS= read -r jit_config
      [[ ${#jit_config} -ge 32 && ${#jit_config} -le 32768 ]] || exit 65
      [[ "$jit_config" =~ ^[A-Za-z0-9_./+=-]+$ ]] || exit 65
      cd /opt/actions-runner
      rm -rf -- _work .docker
      install -d -m 0700 .docker
      cat >.docker/config.json <<'JSON'
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
      chmod 0600 .docker/config.json
      trap 'rm -rf -- /opt/actions-runner/_work /opt/actions-runner/.docker' EXIT
      env -i HOME=/opt/actions-runner PATH=/usr/local/bin:/usr/bin:/bin \
        HTTP_PROXY=http://127.0.0.1:3128 HTTPS_PROXY=http://127.0.0.1:3128 \
        NO_PROXY=localhost,127.0.0.1 \
        ./run.sh --jitconfig "$jit_config"
  - path: /usr/local/sbin/idp-runner-bootstrap
    owner: root:root
    permissions: '0700'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      manifest=/etc/idp-supply-chain/runner-bundle-manifest.json
      mountpoint=/mnt/idp-runner-bundle
      work=/var/tmp/idp-runner-bundle
      asset=$(python3 -c 'import json,urllib.parse; print(urllib.parse.urlparse(json.load(open("/etc/idp-supply-chain/runner-bundle-manifest.json"))["bundle"]["url"]).path.rsplit("/",1)[1])')
      digest=$(python3 -c 'import json; print(json.load(open("/etc/idp-supply-chain/runner-bundle-manifest.json"))["bundle"]["sha256"])')
      mkdir -p "$mountpoint"
      for attempt in $(seq 1 60); do
        [[ -b /dev/sr0 ]] && break
        sleep 2
      done
      [[ -b /dev/sr0 ]] || { echo "runner bundle CD-ROM is unavailable" >&2; exit 69; }
      mount -o ro,nosuid,nodev,noexec /dev/sr0 "$mountpoint"
      bundle="$mountpoint/$asset"
      [[ -f "$bundle" ]] || { echo "runner bundle is absent from read-only media" >&2; exit 69; }
      printf '%s  %s\n' "$digest" "$bundle" | sha256sum --check --strict -
      rm -rf -- "$work"
      mkdir -p -- "$work"
      if tar -tzf "$bundle" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then
        echo "unsafe runner bundle path" >&2
        exit 66
      fi
      tar --extract --gzip --file "$bundle" --directory "$work" --no-same-owner
      [[ -f "$work/install.sh" && ! -L "$work/install.sh" ]] || exit 66
      chmod 0700 "$work/install.sh"
      "$work/install.sh"
      python3 - <<'PY'
      import hashlib, json, os, pathlib
      manifest = json.load(open('/etc/idp-supply-chain/runner-bundle-manifest.json'))
      expected = {'actions-runner', 'cosign', 'docker', 'docker-buildx', 'gh', 'git', 'syft', 'trivy'}
      if set(manifest['tools']) != expected:
          raise SystemExit('runner tool set differs')
      for name, record in manifest['tools'].items():
          path = pathlib.Path(record['path'])
          if not path.is_file() or path.is_symlink():
              raise SystemExit(f'runner tool missing or linked: {name}')
          actual = hashlib.sha256(path.read_bytes()).hexdigest()
          if actual != record['sha256']:
              raise SystemExit(f'runner tool digest mismatch: {name}')
      forbidden = [pathlib.Path('/etc/rancher/k3s/k3s.yaml'), pathlib.Path('/home/idprunner/.kube/config')]
      if any(path.exists() for path in forbidden):
          raise SystemExit('kubeconfig must not exist on the CI runner')
      PY
      runuser -u idprunner -- /usr/local/bin/docker info >/dev/null
      runuser -u idprunner -- /usr/local/bin/docker buildx version >/dev/null
      /usr/local/sbin/idp-egress-policy-apply
      /usr/local/sbin/idp-egress-policy-check --strict
      chown -R idprunner:idprunner /opt/actions-runner
      chmod -R go-w /opt/actions-runner
      rm -rf -- "$work"
      umount "$mountpoint"
      install -o root -g root -m 0444 /dev/null /var/lib/idp-supply-chain-runner-ready
runcmd:
  - [systemctl, restart, ssh]
  - [bash, /usr/local/sbin/idp-runner-bootstrap]
final_message: IDP supply-chain runner bootstrap finished; readiness marker is evidence only after external verification
'@
$userData = $userDataTemplate.Replace("__VM_NAME__", $VmName).Replace("__RESTRICTED_PUBLIC_KEY__", $restrictedPublicKey).Replace("__MANIFEST_BASE64__", $manifestBase64)

$metadata = @"
instance-id: $VmName-001
local-hostname: $VmName
network:
  version: 2
  ethernets:
    enp2s0:
      dhcp4: true
"@
$metadataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($metadata))
$userDataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($userData))

if (-not ("IdpComStreamWriter" -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
public static class IdpComStreamWriter {
  public static void Save(object source, string path) {
    IntPtr unknown = Marshal.GetIUnknownForObject(source);
    try {
      IStream stream = (IStream)Marshal.GetTypedObjectForIUnknown(unknown, typeof(IStream));
      using (FileStream output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
        byte[] buffer = new byte[1024 * 1024];
        IntPtr readPointer = Marshal.AllocCoTaskMem(sizeof(int));
        try {
          while (true) {
            Marshal.WriteInt32(readPointer, 0);
            stream.Read(buffer, buffer.Length, readPointer);
            int read = Marshal.ReadInt32(readPointer);
            if (read <= 0) break;
            output.Write(buffer, 0, read);
          }
        } finally { Marshal.FreeCoTaskMem(readPointer); }
      }
    } finally { Marshal.Release(unknown); }
  }
}
'@
}

function New-RunnerBundleIso([string]$SourceDirectory, [string]$IsoPath) {
    $fileSystemImage = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
    $fileSystemImage.FileSystemsToCreate = 3
    $fileSystemImage.VolumeName = "IDPRUNNER"
    $fileSystemImage.Root.AddTree($SourceDirectory, $false)
    $result = $fileSystemImage.CreateResultImage()
    [IdpComStreamWriter]::Save($result.ImageStream, $IsoPath)
}

$pciBridges = @"
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
pciBridge6.pciSlotNumber = "22"
pciBridge7.present = "TRUE"
pciBridge7.virtualDev = "pcieRootPort"
pciBridge7.pciSlotNumber = "23"
"@

$createdTarget = $false
$vmxPath = Join-Path $resolvedVmDirectory "$VmName.vmx"
try {
    New-Item -ItemType Directory -Path $vmParent -Force | Out-Null
    New-Item -ItemType Directory -Path $resolvedVmDirectory | Out-Null
    $createdTarget = $true
    $diskPath = Join-Path $resolvedVmDirectory "$VmName.vmdk"
    $bundleIsoPath = Join-Path $resolvedVmDirectory "idp-runner-bootstrap.iso"
    New-RunnerBundleIso $bundleSourceDirectory $bundleIsoPath
    if (-not (Test-Path -LiteralPath $bundleIsoPath -PathType Leaf)) { throw "Runner bundle ISO creation failed." }
    & $diskManager -r $resolvedImage -t 0 $diskPath
    if ($LASTEXITCODE -ne 0) { throw "VMware disk conversion failed with exit code $LASTEXITCODE" }
    & $diskManager -x $DiskSize $diskPath
    if ($LASTEXITCODE -ne 0) { throw "VMware disk expansion failed with exit code $LASTEXITCODE" }

    $vmx = @"
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "21"
displayName = "$VmName"
annotation = "Hardened one-job JIT IDP supply-chain runner; no kubeconfig or stored credential"
guestOS = "ubuntu-64"
firmware = "efi"
uefi.secureBoot.enabled = "TRUE"
numvcpus = "$ProcessorCount"
cpuid.coresPerSocket = "$ProcessorCount"
memsize = "$MemoryMb"
tools.syncTime = "TRUE"
sound.present = "FALSE"
usb.present = "FALSE"
sharedFolder.maxNum = "0"
isolation.tools.copy.disable = "TRUE"
isolation.tools.paste.disable = "TRUE"
isolation.tools.dnd.disable = "TRUE"
isolation.tools.hgfs.disable = "TRUE"
$pciBridges
scsi0.present = "TRUE"
scsi0.virtualDev = "lsilogic"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "$VmName.vmdk"
ide1:0.present = "TRUE"
ide1:0.deviceType = "cdrom-image"
ide1:0.fileName = "$bundleIsoPath"
ide1:0.startConnected = "TRUE"
ethernet0.present = "TRUE"
ethernet0.connectionType = "nat"
ethernet0.virtualDev = "vmxnet3"
ethernet0.startConnected = "TRUE"
ethernet0.addressType = "generated"
floppy0.present = "FALSE"
guestinfo.metadata = "$metadataBase64"
guestinfo.metadata.encoding = "base64"
guestinfo.userdata = "$userDataBase64"
guestinfo.userdata.encoding = "base64"
"@
    [System.IO.File]::WriteAllText($vmxPath, $vmx, $utf8NoBom)

    if ($Start) {
        & $vmRun -T ws start $vmxPath nogui
        if ($LASTEXITCODE -ne 0) { throw "VMware VM start failed with exit code $LASTEXITCODE" }
    }

    [pscustomobject]@{
        vm_name = $VmName
        vmx_path = $vmxPath
        image_sha256 = $actualImageSha256
        runner_bundle_sha256 = $manifest.bundle.sha256
        runner_bundle_iso_sha256 = (Get-FileHash -LiteralPath $bundleIsoPath -Algorithm SHA256).Hash.ToLowerInvariant()
        runner_bundle_host = $manifest.bundle.approved_host
        processors = $ProcessorCount
        memory_mb = $MemoryMb
        disk_size = $DiskSize
        network = @("VMnet8_NAT")
        registration = "JIT_STDIN_ONE_JOB"
        kubeconfig_allowed = $false
        stored_credential = $false
        started = [bool]$Start
        runtime_validated = $false
    } | ConvertTo-Json -Depth 4
}
catch {
    if ($createdTarget -and (Test-Path -LiteralPath $resolvedVmDirectory) -and -not (Test-Path -LiteralPath $vmxPath -PathType Leaf)) {
        Remove-Item -LiteralPath $resolvedVmDirectory -Recurse -Force
    }
    throw
}
