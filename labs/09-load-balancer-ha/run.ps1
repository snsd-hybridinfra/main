param(
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\2026-10-15.json')
)

$ErrorActionPreference = 'Stop'
$project = 'news-lab09'
$compose = Join-Path $PSScriptRoot 'compose.yaml'
$tempPublicKey = Join-Path ([System.IO.Path]::GetTempPath()) ("$project-" + [guid]::NewGuid().ToString('N') + '.pub')

function Compose {
    & docker compose -p $project -f $compose @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed: $args" }
}

function Request-Backend {
    $body = & docker compose -p $project -f $compose exec -T client curl -fsS --max-time 3 http://172.31.20.10/
    if ($LASTEXITCODE -ne 0) { throw 'HTTP request through edge failed' }
    "$body".Trim()
}

function Sample([int]$Count) {
    $items = @()
    1..$Count | ForEach-Object {
        $items += Request-Backend
        Start-Sleep -Milliseconds 100
    }
    $items
}

function Counts($Items) {
    @($Items | Group-Object | Sort-Object Name | ForEach-Object {
        [ordered]@{ backend = $_.Name; requests = $_.Count }
    })
}

Compose down --volumes --remove-orphans
try {
    Compose build
    Compose up -d

    $ready = $false
    1..30 | ForEach-Object {
        if (-not $ready) {
            try {
                $status = (& docker inspect -f '{{.State.Health.Status}}' (& docker compose -p $project -f $compose ps -q edge)).Trim()
                if ($status -eq 'healthy') { $ready = $true } else { Start-Sleep -Seconds 1 }
            }
            catch { Start-Sleep -Seconds 1 }
        }
    }
    if (-not $ready) { throw 'edge container did not become healthy' }

    Compose exec -T admin sh -lc 'rm -f /tmp/lab_key /tmp/lab_key.pub; ssh-keygen -q -t ed25519 -N "" -f /tmp/lab_key'

    $adminId = (& docker compose -p $project -f $compose ps -q admin).Trim()
    $edgeId = (& docker compose -p $project -f $compose ps -q edge).Trim()
    if (-not $adminId -or -not $edgeId) { throw 'container id lookup failed' }

    & docker cp "${adminId}:/tmp/lab_key.pub" $tempPublicKey
    if ($LASTEXITCODE -ne 0) { throw 'failed to copy test public key from admin' }
    & docker cp $tempPublicKey "${edgeId}:/home/lab/.ssh/authorized_keys"
    if ($LASTEXITCODE -ne 0) { throw 'failed to install test public key on edge' }
    Compose exec -T edge sh -lc 'chown lab:lab /home/lab/.ssh/authorized_keys; chmod 600 /home/lab/.ssh/authorized_keys'

    $managementOutput = & docker compose -p $project -f $compose exec -T admin ssh -i /tmp/lab_key -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 lab@172.31.10.10 'printf management-ssh-ok' 2>$null
    $managementExit = $LASTEXITCODE
    $managementText = "$managementOutput".Trim()

    $null = & docker compose -p $project -f $compose exec -T client ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 lab@172.31.20.10 true 2>$null
    $dataSshExit = $LASTEXITCODE

    $otOperatorOutput = ''
    $otOperatorExit = 1
    1..20 | ForEach-Object {
        if ($otOperatorExit -ne 0) {
            $otOperatorOutput = & docker compose -p $project -f $compose exec -T ot-operator curl -fsS --max-time 2 http://172.31.30.30/ 2>$null
            $otOperatorExit = $LASTEXITCODE
            if ($otOperatorExit -ne 0) { Start-Sleep -Milliseconds 250 }
        }
    }
    $otOperatorText = "$otOperatorOutput".Trim()

    $null = & docker compose -p $project -f $compose exec -T client curl -fsS --max-time 2 http://172.31.30.30/ 2>$null
    $dataToOtExit = $LASTEXITCODE
    $null = & docker compose -p $project -f $compose exec -T admin curl -fsS --max-time 2 http://172.31.30.30/ 2>$null
    $managementToOtExit = $LASTEXITCODE

    $normal = @(Sample 8)
    Compose stop web01
    $duringFailure = @(Sample 8)
    Compose start web01

    $rejoined = $false
    1..30 | ForEach-Object {
        if (-not $rejoined) {
            if ((Request-Backend) -eq 'web01') { $rejoined = $true }
            else { Start-Sleep -Milliseconds 250 }
        }
    }
    if (-not $rejoined) { throw 'web01 did not rejoin the pool' }
    $afterRecovery = @(Sample 8)

    $normalNames = @($normal | Sort-Object -Unique)
    $failureNames = @($duringFailure | Sort-Object -Unique)
    $recoveryNames = @($afterRecovery | Sort-Object -Unique)

    $assertions = [ordered]@{
        admin_to_management_ssh_allowed = (($managementExit -eq 0) -and ($managementText -eq 'management-ssh-ok'))
        data_network_to_ssh_denied = ($dataSshExit -ne 0)
        ot_operator_to_controller_allowed = (($otOperatorExit -eq 0) -and ($otOperatorText -eq 'ot-controller-ok'))
        data_network_to_ot_controller_denied = ($dataToOtExit -ne 0)
        management_network_to_ot_controller_denied = ($managementToOtExit -ne 0)
        both_backends_seen_before_failure = ($normalNames.Count -eq 2)
        only_web02_seen_during_web01_failure = (($failureNames.Count -eq 1) -and ($failureNames[0] -eq 'web02'))
        both_backends_seen_after_recovery = ($recoveryNames.Count -eq 2)
    }
    $passed = -not ($assertions.Values -contains $false)

    $result = [ordered]@{
        tested_at = (Get-Date).ToUniversalTime().ToString('o')
        scope = 'local-container-management-data-ot-separation-and-backend-failover'
        source = [ordered]@{
            citrix_security_bulletin = 'https://support.citrix.com/external/article/CTX697096'
            citrix_security_bulletin_published = '2026-09-27'
            cisco_sdwan_advisory = 'https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-sdwan-webauth-xr8beuuU'
            cisco_sdwan_advisory_published = '2026-09-30'
            management_data_separation = 'https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/mgmt-and-data-plane-separation.html'
            cert_fr_ot_alert = 'https://cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-012/'
            cert_fr_ot_alert_published = '2026-10-12'
            ap_refrigeration_incident = 'https://apnews.com/article/france-supermarkets-hacked-cybercrime-81c2d5721f4df77f601f71741ef7c291'
            ap_report_published = '2026-10-14'
            incident_date = '2026-10-12'
        }
        environment = [ordered]@{
            runtime = 'Docker Desktop'
            edge_image_id = (& docker inspect -f '{{.Image}}' $edgeId).Trim()
            management_network = '172.31.10.0/24'
            data_network = '172.31.20.0/24'
            ot_network = '172.31.30.0/24'
            management_ssh = '172.31.10.10:22'
            data_http = '172.31.20.10:80'
        }
        access_tests = [ordered]@{
            admin_to_management_ssh = [ordered]@{ exit_code = $managementExit; output = $managementText }
            data_client_to_data_ip_ssh = [ordered]@{ exit_code = $dataSshExit; expected = 'non-zero because SSH is not bound to the data-plane address' }
            ot_operator_to_controller = [ordered]@{ exit_code = $otOperatorExit; output = $otOperatorText }
            data_client_to_ot_controller = [ordered]@{ exit_code = $dataToOtExit; expected = 'non-zero because the data container is not attached to the OT network' }
            management_admin_to_ot_controller = [ordered]@{ exit_code = $managementToOtExit; expected = 'non-zero because the management container is not attached to the OT network' }
        }
        http_tests = [ordered]@{
            normal = [ordered]@{ samples = $normal; counts = @(Counts $normal) }
            web01_stopped = [ordered]@{ samples = $duringFailure; counts = @(Counts $duringFailure) }
            web01_restarted = [ordered]@{ samples = $afterRecovery; counts = @(Counts $afterRecovery) }
        }
        assertions = $assertions
        passed = $passed
        not_validated = @(
            'Citrix NetScaler ADC or Gateway',
            'CVE-2026-88771 through CVE-2026-88778',
            'Cisco Catalyst SD-WAN Manager or CVE-2026-76504',
            'HTTPS/API authentication bypass, compromise hunting, or fixed software upgrade',
            'NetScaler NSIP, SNIP, VIP, ACL, secure management routing tables, or HA pair',
            'Danfoss, Copeland, or any refrigeration controller, firmware, protocol, or exploit'
            'Production firewall, VPN, jump host, identity-aware proxy, OT monitoring, or emergency local control'
            'Internet exposure, TLS, WAF, VPN, AAA, exploit, or performance'
        )
    }

    $directory = Split-Path -Parent $EvidencePath
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidencePath -Encoding utf8NoBOM
    $result | ConvertTo-Json -Depth 8
    if (-not $passed) { exit 1 }
}
finally {
    if (Test-Path -LiteralPath $tempPublicKey) { Remove-Item -LiteralPath $tempPublicKey -Force }
    Compose down --volumes --remove-orphans
}
