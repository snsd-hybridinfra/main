param(
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\2026-09-29.json')
)

$ErrorActionPreference = 'Stop'
$project = 'news-lab03'
$compose = Join-Path $PSScriptRoot 'compose.yaml'
$password = 'synthetic-' + [guid]::NewGuid().ToString('N')

function Compose {
    & docker compose -p $project -f $compose @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed: $args" }
}

$env:IOSXE_MOCK_PASSWORD = $password
Compose down --volumes --remove-orphans
try {
    Compose build
    Compose up -d

    $ready = $false
    1..30 | ForEach-Object {
        if (-not $ready) {
            $null = & docker compose -p $project -f $compose exec -T runner python3 -c "import socket; s=socket.create_connection(('device', 443), 1); s.close()" 2>$null
            if ($LASTEXITCODE -eq 0) { $ready = $true } else { Start-Sleep -Seconds 1 }
        }
    }
    if (-not $ready) { throw 'synthetic RESTCONF device did not become ready' }

    $successOutput = @(& docker compose -p $project -f $compose exec -T -e IOSXE_USER=iosxe -e "IOSXE_PASSWORD=$password" runner python3 /lab/compare.py --host device --local-insecure-tls 2>&1)
    $successExit = $LASTEXITCODE
    if ($successExit -ne 0) { throw "comparison failed with exit code $successExit`: $($successOutput -join ' ')" }
    $comparison = ($successOutput -join [Environment]::NewLine) | ConvertFrom-Json
    $collectedUtc = ([DateTimeOffset]$comparison.collected_at_utc).ToUniversalTime().ToString('o')
    $comparison | Add-Member -NotePropertyName collected_at_utc -NotePropertyValue $collectedUtc -Force

    $deniedOutput = @(& docker compose -p $project -f $compose exec -T -e IOSXE_USER=iosxe -e IOSXE_PASSWORD=wrong-password runner python3 /lab/compare.py --host device --local-insecure-tls 2>&1)
    $deniedExit = $LASTEXITCODE

    $assertions = [ordered]@{
        restconf_and_cli_collected = (($comparison.api_count -eq 3) -and ($comparison.cli_count -eq 3))
        common_interfaces_compared = ($comparison.compared -eq 3)
        statuses_match = ($comparison.mismatches -eq 0)
        no_one_sided_interfaces = (($comparison.api_only.Count -eq 0) -and ($comparison.cli_only.Count -eq 0))
        invalid_credentials_rejected = ($deniedExit -eq 2)
    }
    $passed = -not ($assertions.Values -contains $false)

    $result = [ordered]@{
        tested_at = (Get-Date).ToUniversalTime().ToString('o')
        scope = 'local-synthetic-iosxe-restconf-and-ssh-cli'
        source = 'Nokia automation announcement, 2026-09-17'
        environment = [ordered]@{
            runtime = 'Docker Desktop'
            restconf = 'HTTPS read-only synthetic IOS XE endpoint'
            cli = 'SSH read-only synthetic IOS XE shell'
        }
        comparison = $comparison
        denied_path = [ordered]@{
            invalid_password_exit_code = $deniedExit
            message = (($deniedOutput -join ' ').Trim())
        }
        assertions = $assertions
        passed = $passed
        not_validated = @(
            'Cisco IOS XE or Nokia/Microsoft products',
            'A physical or virtual network device',
            'Production certificate trust, AAA, configuration writes, or telemetry',
            'API and CLI collection against a changing live device'
        )
    }

    $directory = Split-Path -Parent $EvidencePath
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $EvidencePath -Encoding utf8NoBOM
    $result | ConvertTo-Json -Depth 10
    if (-not $passed) { exit 1 }
}
finally {
    Remove-Item Env:IOSXE_MOCK_PASSWORD -ErrorAction SilentlyContinue
    Compose down --volumes --remove-orphans
}
