[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath,

    [Parameter(Mandatory = $true)]
    [string]$VmDirectory,

    [Parameter(Mandatory = $true)]
    [string]$PublicKeyPath,

    [string]$VmName = "snsd-ansible-control",
    [int]$MemoryMb = 4096,
    [int]$ProcessorCount = 2,
    [string]$DiskSize = "30GB",
    [switch]$RepairExisting,
    [switch]$Start
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$expectedImageSha256 = "b9dc4dea4bdb09c1e08e40cce34fbd3d8fe252ff71bd9be979ef8b15256d80e8"
$vmwareRoot = "C:\Program Files (x86)\VMware\VMware Workstation"
$diskManager = Join-Path $vmwareRoot "vmware-vdiskmanager.exe"
$vmRun = Join-Path $vmwareRoot "vmrun.exe"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$pciBridgeConfiguration = @"
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
"@

if (-not (Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
    throw "Reviewed Ubuntu image is missing: $ImagePath"
}
if (-not (Test-Path -LiteralPath $PublicKeyPath -PathType Leaf)) {
    throw "Public SSH key is missing: $PublicKeyPath"
}
foreach ($tool in @($diskManager, $vmRun)) {
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
        throw "Required VMware tool is missing: $tool"
    }
}
if ($MemoryMb -lt 2048 -or $MemoryMb -gt 8192) {
    throw "MemoryMb must remain between 2048 and 8192."
}
if ($ProcessorCount -lt 1 -or $ProcessorCount -gt 4) {
    throw "ProcessorCount must remain between 1 and 4."
}
if ($DiskSize -notmatch "^(2[0-9]|3[0-9]|40)GB$") {
    throw "DiskSize must remain between 20GB and 40GB."
}

$resolvedImage = (Resolve-Path -LiteralPath $ImagePath).Path
$actualImageSha256 = (Get-FileHash -LiteralPath $resolvedImage -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualImageSha256 -ne $expectedImageSha256) {
    throw "Reviewed Ubuntu image checksum mismatch: $actualImageSha256"
}

$resolvedVmDirectory = [System.IO.Path]::GetFullPath($VmDirectory)
if ($RepairExisting) {
    $existingVmxPath = Join-Path $resolvedVmDirectory "$VmName.vmx"
    if (-not (Test-Path -LiteralPath $existingVmxPath -PathType Leaf)) {
        throw "Existing VMX is missing: $existingVmxPath"
    }
    $runningVms = @(& $vmRun -T ws list)
    if ($runningVms -contains $existingVmxPath) {
        throw "Refusing to repair a running VM: $existingVmxPath"
    }
    $existingLines = [System.IO.File]::ReadAllLines($existingVmxPath)
    $preservedLines = @($existingLines | Where-Object {
        $_ -notmatch '^pciBridge[0-7]\.' -and
        $_ -notmatch '^ethernet[01]\.pciSlotNumber\s*='
    })
    $repairedVmx = (($preservedLines + $pciBridgeConfiguration.TrimEnd()) -join [Environment]::NewLine) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($existingVmxPath, $repairedVmx, $utf8NoBom)
    [pscustomobject]@{
        vm_name = $VmName
        vmx_path = $existingVmxPath
        repaired_pcie_root_ports = $true
        started = $false
    } | ConvertTo-Json
    return
}
if (Test-Path -LiteralPath $resolvedVmDirectory) {
    throw "VM target already exists; refusing to overwrite: $resolvedVmDirectory"
}
$vmParent = Split-Path -Parent $resolvedVmDirectory
New-Item -ItemType Directory -Path $vmParent -Force | Out-Null
New-Item -ItemType Directory -Path $resolvedVmDirectory | Out-Null

$publicKey = (Get-Content -LiteralPath $PublicKeyPath -Raw).Trim()
if ($publicKey -notmatch "^ssh-ed25519 [A-Za-z0-9+/=]+ [A-Za-z0-9@._-]+$") {
    throw "The reviewed public key must be a single ED25519 public key."
}

$diskPath = Join-Path $resolvedVmDirectory "$VmName.vmdk"
$vmxPath = Join-Path $resolvedVmDirectory "$VmName.vmx"

& $diskManager -r $resolvedImage -t 0 $diskPath
if ($LASTEXITCODE -ne 0) {
    throw "VMware disk conversion failed with exit code $LASTEXITCODE"
}
& $diskManager -x $DiskSize $diskPath
if ($LASTEXITCODE -ne 0) {
    throw "VMware disk expansion failed with exit code $LASTEXITCODE"
}

$metadata = @"
instance-id: snsd-ansible-control-001
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
  - name: ztansible
    gecos: Zero Trust Ansible Controller
    groups: [adm, sudo, users]
    shell: /bin/bash
    lock_passwd: true
    sudo:
      - ALL=(root) NOPASSWD:/usr/bin/apt-get, /usr/bin/apt, /usr/bin/systemctl, /usr/sbin/netplan, /usr/sbin/ufw
    ssh_authorized_keys:
      - $publicKey
growpart:
  mode: auto
  devices: ['/']
resize_rootfs: true
package_update: true
package_upgrade: false
packages:
  - ansible-core
  - ca-certificates
  - git
  - openssh-server
  - python3
  - ufw
write_files:
  - path: /etc/ssh/sshd_config.d/60-snsd-control-node.conf
    owner: root:root
    permissions: '0644'
    content: |
      PasswordAuthentication no
      KbdInteractiveAuthentication no
      PermitRootLogin no
      AllowUsers ztansible
runcmd:
  - [systemctl, restart, ssh]
  - [ufw, default, deny, incoming]
  - [ufw, default, allow, outgoing]
  - [ufw, allow, from, 192.168.8.0/24, to, any, port, '22', proto, tcp]
  - [ufw, allow, from, 192.168.1.0/24, to, any, port, '22', proto, tcp]
  - [ufw, --force, enable]
  - [touch, /var/lib/snsd-ansible-control-ready]
final_message: SNSD Ansible control node initialization complete
"@

$metadataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($metadata))
$userDataBase64 = [Convert]::ToBase64String($utf8NoBom.GetBytes($userData))
$vmx = @"
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "21"
displayName = "$VmName"
annotation = "Bounded non-production Ansible control node; NAT and host-only only"
guestOS = "ubuntu-64"
firmware = "efi"
uefi.secureBoot.enabled = "TRUE"
numvcpus = "$ProcessorCount"
cpuid.coresPerSocket = "$ProcessorCount"
memsize = "$MemoryMb"
mem.hotadd = "FALSE"
tools.syncTime = "TRUE"
tools.upgrade.policy = "manual"
sound.present = "FALSE"
usb.present = "FALSE"
sharedFolder.maxNum = "0"
isolation.tools.copy.disable = "TRUE"
isolation.tools.paste.disable = "TRUE"
isolation.tools.dnd.disable = "TRUE"
isolation.tools.hgfs.disable = "TRUE"
$pciBridgeConfiguration
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

[pscustomobject]@{
    vm_name = $VmName
    vmx_path = $vmxPath
    image_sha256 = $actualImageSha256
    processors = $ProcessorCount
    memory_mb = $MemoryMb
    disk_size = $DiskSize
    network = @("VMnet8_NAT", "VMnet1_HOST_ONLY")
    password_authentication = $false
    root_ssh = $false
    shared_folders = $false
    started = [bool]$Start
} | ConvertTo-Json -Depth 4
