[CmdletBinding()]
param(
    [string]$KindPath = "kind",
    [string]$ClusterName = "news-rbac-lab",
    [switch]$KeepCluster,
    [string]$EvidencePath = (Join-Path $PSScriptRoot "evidence\2026-09-30.json")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$nodeImage = "kindest/node:v1.36.4@sha256:099e049362a1526b2db71494e1947aae99bd16290d7c895f2b7ea312e3cbfaed"
$manifestPath = Join-Path $PSScriptRoot "manifests\rbac-lab.yaml"
$kubeconfigPath = Join-Path ([System.IO.Path]::GetTempPath()) "$ClusterName-kubeconfig"
$subject = "system:serviceaccount:rbac-lab:operator-reader"
$clusterCreated = $false

function Invoke-Kubectl {
    param([string[]]$CommandArgs, [int[]]$AllowedExitCodes = @(0))
    $output = & kubectl --kubeconfig $kubeconfigPath @CommandArgs 2>&1
    if ($LASTEXITCODE -notin $AllowedExitCodes) {
        throw "kubectl failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join [Environment]::NewLine).Trim()
}

function Test-Permission {
    param(
        [string]$Name,
        [string]$Verb,
        [string]$Resource,
        [string]$Namespace,
        [string]$Expected
    )

    $arguments = @("auth", "can-i", $Verb, $Resource, "--as", $subject)
    if ($Namespace) {
        $arguments += @("--namespace", $Namespace)
    }
    $raw = Invoke-Kubectl -CommandArgs $arguments -AllowedExitCodes @(0, 1)
    $actual = @($raw -split "\r?\n" | Where-Object { $_ -match "^(yes|no)$" })[-1]
    [pscustomobject]@{
        name = $Name
        verb = $Verb
        resource = $Resource
        namespace = $Namespace
        expected = $Expected
        actual = $actual
        passed = ($actual -eq $Expected)
    }
}

try {
    if (-not (Test-Path -LiteralPath $KindPath)) {
        $resolved = Get-Command $KindPath -ErrorAction SilentlyContinue
        if (-not $resolved) {
            throw "kind 실행 파일을 찾지 못했습니다. -KindPath로 경로를 지정하세요."
        }
        $KindPath = $resolved.Source
    }

    $existing = & $KindPath get clusters 2>$null
    if ($existing -contains $ClusterName) {
        & $KindPath delete cluster --name $ClusterName | Out-Null
    }

    & $KindPath create cluster --name $ClusterName --image $nodeImage --wait 180s --kubeconfig $kubeconfigPath
    if ($LASTEXITCODE -ne 0) {
        throw "kind cluster 생성에 실패했습니다."
    }
    $clusterCreated = $true

    Invoke-Kubectl -CommandArgs @("apply", "-f", $manifestPath) | Out-Null
    $version = Invoke-Kubectl -CommandArgs @("version", "-o", "json") | ConvertFrom-Json
    $role = Invoke-Kubectl -CommandArgs @("get", "role", "workload-observer", "-n", "rbac-lab", "-o", "json") | ConvertFrom-Json

    $checks = @(
        Test-Permission -Name "same-namespace-pod-read" -Verb "get" -Resource "pods" -Namespace "rbac-lab" -Expected "yes"
        Test-Permission -Name "same-namespace-deployment-list" -Verb "list" -Resource "deployments.apps" -Namespace "rbac-lab" -Expected "yes"
        Test-Permission -Name "secret-read-denied" -Verb "get" -Resource "secrets" -Namespace "rbac-lab" -Expected "no"
        Test-Permission -Name "pod-delete-denied" -Verb "delete" -Resource "pods" -Namespace "rbac-lab" -Expected "no"
        Test-Permission -Name "other-namespace-list-denied" -Verb "list" -Resource "pods" -Namespace "other-team" -Expected "no"
        Test-Permission -Name "clusterrole-read-denied" -Verb "get" -Resource "clusterroles.rbac.authorization.k8s.io" -Namespace "" -Expected "no"
    )

    $passedCount = @($checks | Where-Object passed).Count
    $report = [ordered]@{
        tested_at = [DateTime]::UtcNow.ToString("o")
        status = if ($passedCount -eq $checks.Count) { "passed" } else { "failed" }
        environment = [ordered]@{
            kind = (& $KindPath version).Trim()
            kubectl_client = $version.clientVersion.gitVersion
            kubernetes_server = $version.serverVersion.gitVersion
            node_image = $nodeImage
        }
        subject = $subject
        role_scope = "namespace:rbac-lab"
        applied_role_rules = $role.rules
        summary = [ordered]@{
            total = $checks.Count
            passed = $passedCount
            failed = $checks.Count - $passedCount
        }
        checks = $checks
    }

    $parent = Split-Path -Parent $EvidencePath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
    $report | ConvertTo-Json -Depth 12

    if ($report.status -ne "passed") {
        exit 1
    }
}
finally {
    if ($clusterCreated -and -not $KeepCluster) {
        & $KindPath delete cluster --name $ClusterName | Out-Null
    }
    Remove-Item -LiteralPath $kubeconfigPath -Force -ErrorAction SilentlyContinue
}
