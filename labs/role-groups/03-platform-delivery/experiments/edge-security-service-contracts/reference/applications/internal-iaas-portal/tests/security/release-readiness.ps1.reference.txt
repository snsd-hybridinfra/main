param(
    [string]$ManifestRoot = (Join-Path $PSScriptRoot '..\..\kubernetes')
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = Resolve-Path $ManifestRoot
$files = Get-ChildItem -Path $resolvedRoot -Recurse -File -Include *.yaml,*.yml

$rules = [ordered]@{
    'zero image digest' = '@sha256:0{64}'
    'example container registry' = 'registry\.example\.com'
    'example public identity host' = 'https://id\.example\.com'
    'placeholder private DNS' = '\.(?:control|cluster)\.internal'
    'placeholder CIDR annotation' = 'replace-cidr'
    'unreviewed lab CIDR' = '(?:10\.0\.0\.0/16|10\.0\.32\.0/20|10\.200\.0\.0/16)'
}

$blockers = [System.Collections.Generic.List[string]]::new()
foreach ($file in $files) {
    $relative = $file.FullName.Substring($resolvedRoot.Path.Length).TrimStart('\')
    foreach ($rule in $rules.GetEnumerator()) {
        $matches = Select-String -Path $file.FullName -Pattern $rule.Value -Encoding utf8
        foreach ($match in $matches) {
            $blockers.Add("$($rule.Key): $relative`:$($match.LineNumber)")
        }
    }
}

if ($blockers.Count -gt 0) {
    Write-Output 'RELEASE READINESS: NO-GO'
    $blockers | Sort-Object -Unique | ForEach-Object { Write-Output "- $_" }
    Write-Output 'Replace every blocker with approved team handoff values before cluster apply.'
    exit 2
}

Write-Output 'RELEASE READINESS: STATIC GO'
Write-Output 'Static GO does not replace image signature, External Secret, cluster dry-run, or network-path verification.'
