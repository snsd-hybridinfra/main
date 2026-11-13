$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$restore = Get-Content -Raw -Encoding utf8 (Join-Path $root 'recovery\integrated\restore-from-restic.sh')
$backup = Get-Content -Raw -Encoding utf8 (Join-Path $root 'backup\scripts\backup-postgres.sh')
$maintenance = Get-Content -Raw -Encoding utf8 (Join-Path $root 'backup\scripts\restic-maintenance.sh')
$maintenanceService = Get-Content -Raw -Encoding utf8 (Join-Path $root 'backup\systemd\iaas-restic-maintenance.service')
$appendOnly = Get-Content -Raw -Encoding utf8 (Join-Path $root 'backup\verification\verify-append-only.sh')

$requiredRestore = @(
    'must end in _restore',
    'sha256sum --check',
    'pg_restore --list',
    '--single-transaction',
    'created_database=false'
)
foreach ($value in $requiredRestore) {
    if (-not $restore.Contains($value)) { throw "restore safeguard missing: $value" }
}

$requiredBackup = @(
    '--format=custom',
    '--no-owner',
    '--no-privileges',
    'RESTIC_PASSWORD_FILE',
    'flock -w'
)
foreach ($value in $requiredBackup) {
    if (-not $backup.Contains($value)) { throw "backup control missing: $value" }
}

if ($backup.Contains('restic forget') -or $backup.Contains('restic prune')) {
    throw 'retention or prune must not run inside the daily database backup'
}

$requiredMaintenance = @(
    'for db_kind in request-db control-db',
    'restic forget',
    'restic prune',
    'restic check',
    'flock -w',
    '--keep-within-daily',
    'RESTIC_MAINTENANCE_MODE'
)
foreach ($value in $requiredMaintenance) {
    if (-not $maintenance.Contains($value)) { throw "maintenance control missing: $value" }
}

if (-not $maintenanceService.Contains('/etc/iaas-backup/maintenance.env') -or
    $maintenanceService.Contains('EnvironmentFile=/etc/iaas-backup/common.env')) {
    throw 'maintenance unit must use its isolated full-access environment'
}

foreach ($value in @('append-only-canary', 'restic forget', '403|forbidden|denied')) {
    if (-not $appendOnly.Contains($value)) { throw "append-only verification missing: $value" }
}

Write-Output 'backup/recovery static policy: PASS'
