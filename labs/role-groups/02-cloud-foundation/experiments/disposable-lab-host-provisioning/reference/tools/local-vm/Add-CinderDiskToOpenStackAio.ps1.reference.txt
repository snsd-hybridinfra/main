[CmdletBinding()]
param(
    [string]$VmxPath = [Text.Encoding]::UTF8.GetString(
        [Convert]::FromBase64String('Rjpc7Y+s7Yq47Y+066as7JikXG9wZW5zdGFjay1haW9cU05TRC1PcGVuU3RhY2stQUlPLnZteA==')
    ),
    [ValidateRange(40, 200)]
    [int]$DiskSizeGb = 100,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$vmrun = 'C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe'
$vdiskManager = 'C:\Program Files (x86)\VMware\VMware Workstation\vmware-vdiskmanager.exe'
$expectedDirectory = [IO.Path]::GetFullPath(
    [Text.Encoding]::UTF8.GetString(
        [Convert]::FromBase64String('Rjpc7Y+s7Yq47Y+066as7JikXG9wZW5zdGFjay1haW8=')
    )
)
$resolvedVmx = [IO.Path]::GetFullPath($VmxPath)
$vmDirectory = [IO.Path]::GetDirectoryName($resolvedVmx)
$diskName = 'SNSD-OpenStack-AIO-cinder.vmdk'
$diskPath = Join-Path $vmDirectory $diskName

if ($vmDirectory -ne $expectedDirectory) {
    throw "Refusing a VM outside the exact approved directory: $vmDirectory"
}
foreach ($path in @($resolvedVmx, $vmrun, $vdiskManager)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required file is missing: $path"
    }
}

$running = & $vmrun list
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to query the VMware running-VM list.'
}
if ($running -contains $resolvedVmx) {
    throw 'Refusing disk attachment while the OpenStack AIO VM is running.'
}

$vmxText = [IO.File]::ReadAllText($resolvedVmx)
if ($vmxText -notmatch '(?mi)^scsi0\.present\s*=\s*"TRUE"\s*$') {
    throw 'The reviewed SCSI controller is not present.'
}
if ($vmxText -match '(?mi)^scsi0:2\.(?:present|fileName)\s*=') {
    if (
        $vmxText -match '(?mi)^scsi0:2\.present\s*=\s*"TRUE"\s*$' -and
        $vmxText -match '(?mi)^scsi0:2\.fileName\s*=\s*"SNSD-OpenStack-AIO-cinder\.vmdk"\s*$' -and
        (Test-Path -LiteralPath $diskPath -PathType Leaf)
    ) {
        Write-Output 'Cinder disk is already attached at the reviewed SCSI slot.'
        exit 0
    }
    throw 'SCSI slot 0:2 is already configured with an unexpected value.'
}
if (Test-Path -LiteralPath $diskPath) {
    throw 'A detached file already exists at the reviewed Cinder disk path.'
}

if (-not $Apply) {
    Write-Output "DRY RUN: create a $DiskSizeGb GiB thin disk and attach it at SCSI 0:2."
    exit 0
}

$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$backupPath = "$resolvedVmx.pre-cinder-$stamp.bak"
$temporaryVmx = "$resolvedVmx.pre-cinder-$stamp.tmp"
$diskCreated = $false
$backupCreated = $false

try {
    Copy-Item -LiteralPath $resolvedVmx -Destination $backupPath
    $backupCreated = $true

    & $vdiskManager -c -s "${DiskSizeGb}GB" -a lsilogic -t 0 $diskPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $diskPath -PathType Leaf)) {
        throw 'VMware virtual-disk creation failed.'
    }
    $diskCreated = $true

    $addition = @(
        'scsi0:2.present = "TRUE"',
        "scsi0:2.fileName = `"$diskName`"",
        'scsi0:2.deviceType = "disk"'
    )
    $updated = $vmxText.TrimEnd("`r", "`n") + "`r`n" + ($addition -join "`r`n") + "`r`n"
    [IO.File]::WriteAllText($temporaryVmx, $updated, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporaryVmx -Destination $resolvedVmx -Force

    $verified = [IO.File]::ReadAllText($resolvedVmx)
    if (
        $verified -notmatch '(?mi)^scsi0:2\.present\s*=\s*"TRUE"\s*$' -or
        $verified -notmatch '(?mi)^scsi0:2\.fileName\s*=\s*"SNSD-OpenStack-AIO-cinder\.vmdk"\s*$'
    ) {
        throw 'The updated VMX did not retain the exact Cinder disk attachment.'
    }

    Write-Output "Cinder disk attachment: PASS ($DiskSizeGb GiB thin, SCSI 0:2)"
    Write-Output "VMX backup retained: $backupPath"
}
catch {
    if (Test-Path -LiteralPath $temporaryVmx) {
        Remove-Item -LiteralPath $temporaryVmx -Force
    }
    if ($backupCreated -and (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
        Copy-Item -LiteralPath $backupPath -Destination $resolvedVmx -Force
    }
    if ($diskCreated -and (Test-Path -LiteralPath $diskPath -PathType Leaf)) {
        Remove-Item -LiteralPath $diskPath -Force
    }
    throw
}
