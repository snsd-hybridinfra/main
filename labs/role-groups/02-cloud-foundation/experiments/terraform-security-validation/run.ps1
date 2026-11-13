param(
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\2026-10-06.json')
)

$ErrorActionPreference = 'Stop'
$checkovImage = 'bridgecrew/checkov:3.3.21'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("news-lab14-" + [guid]::NewGuid().ToString('N'))

function Invoke-TerraformCheck {
    param([string]$Name)

    $source = Join-Path $PSScriptRoot $Name
    $target = Join-Path $tempRoot $Name
    Copy-Item -LiteralPath $source -Destination $target -Recurse

    & terraform "-chdir=$target" init -backend=false -input=false -no-color | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "terraform init failed for $Name with exit code $LASTEXITCODE"
    }

    $validateRaw = & terraform "-chdir=$target" validate -json
    if ($LASTEXITCODE -ne 0) {
        throw "terraform validate failed for $Name with exit code $LASTEXITCODE"
    }
    return ($validateRaw -join "`n" | ConvertFrom-Json)
}

function Invoke-CheckovScan {
    param([string]$Name)

    $mount = $PSScriptRoot.Replace('\', '/')
    $raw = & docker run --rm --volume "${mount}:/tf:ro" $checkovImage `
        --directory "/tf/$Name" `
        --framework terraform `
        --check CKV_AWS_24 `
        --output json `
        --quiet
    $exitCode = $LASTEXITCODE
    $parsed = ($raw -join "`n" | ConvertFrom-Json)
    return [pscustomobject]@{
        exit_code = $exitCode
        passed = [int]$parsed.summary.passed
        failed = [int]$parsed.summary.failed
        failed_checks = @($parsed.results.failed_checks | ForEach-Object {
            [ordered]@{
                check_id = $_.check_id
                check_name = $_.check_name
                resource = $_.resource
                file = $_.file_path
                file_line_range = @($_.file_line_range)
            }
        })
        selected_check = 'CKV_AWS_24'
    }
}

New-Item -ItemType Directory -Path $tempRoot | Out-Null
try {
    & terraform fmt -check -recursive $PSScriptRoot
    if ($LASTEXITCODE -ne 0) {
        throw "terraform fmt check failed with exit code $LASTEXITCODE"
    }

    $terraformVersion = (& terraform version -json | ConvertFrom-Json).terraform_version
    $beforeValidate = Invoke-TerraformCheck -Name 'before'
    $afterValidate = Invoke-TerraformCheck -Name 'after'
    $beforeScan = Invoke-CheckovScan -Name 'before'
    $afterScan = Invoke-CheckovScan -Name 'after'
    $checkovRepoDigest = (& docker image inspect $checkovImage --format '{{index .RepoDigests 0}}').Trim()
    if ($LASTEXITCODE -ne 0 -or -not $checkovRepoDigest) {
        throw 'failed to resolve the Checkov image digest'
    }

    $assertions = [ordered]@{
        terraform_before_is_valid = [bool]$beforeValidate.valid
        terraform_after_is_valid = [bool]$afterValidate.valid
        public_ssh_is_detected = (
            $beforeScan.exit_code -eq 1 -and
            $beforeScan.failed -eq 1 -and
            $beforeScan.failed_checks[0].check_id -eq 'CKV_AWS_24'
        )
        restricted_ssh_passes_same_check = (
            $afterScan.exit_code -eq 0 -and
            $afterScan.failed -eq 0 -and
            $afterScan.passed -eq 1 -and
            $afterScan.selected_check -eq 'CKV_AWS_24'
        )
    }
    $passed = -not ($assertions.Values -contains $false)

    $result = [ordered]@{
        tested_at = [DateTimeOffset]::UtcNow.ToString('o')
        scope = 'local-terraform-static-security-validation'
        sources = @(
            [ordered]@{
                title = 'AWS Continuum sets a new standard in autonomous code security'
                url = 'https://aws.amazon.com/blogs/security/aws-continuum-sets-a-new-standard-in-autonomous-code-security/'
                published = '2026-10-05'
            },
            [ordered]@{
                title = 'Changing the game: Using agentic AI to secure infrastructure code'
                url = 'https://cloud.google.com/blog/topics/systems/using-ai-agents-to-secure-google-infrastructure'
                published = '2026-09-18'
            }
        )
        environment = [ordered]@{
            terraform_version = $terraformVersion
            checkov_image = $checkovImage
            checkov_image_digest = $checkovRepoDigest
            cloud_credentials_used = $false
            terraform_apply_run = $false
        }
        before = [ordered]@{
            terraform_valid = [bool]$beforeValidate.valid
            checkov_exit_code = $beforeScan.exit_code
            passed_checks = $beforeScan.passed
            failed_checks = $beforeScan.failed
            findings = $beforeScan.failed_checks
        }
        after = [ordered]@{
            terraform_valid = [bool]$afterValidate.valid
            checkov_exit_code = $afterScan.exit_code
            selected_check = $afterScan.selected_check
            passed_checks = $afterScan.passed
            failed_checks = $afterScan.failed
        }
        assertions = $assertions
        passed = $passed
        not_validated = @(
            'AWS authentication, terraform plan, or terraform apply',
            'A deployed Security Group or real network reachability',
            'AWS Continuum or Google internal security agents',
            'Checks other than the selected public SSH rule CKV_AWS_24',
            'CI enforcement, human approval, drift detection, or rollback'
        )
    }

    $rendered = $result | ConvertTo-Json -Depth 12
    New-Item -ItemType Directory -Path (Split-Path -Parent $EvidencePath) -Force | Out-Null
    [IO.File]::WriteAllText($EvidencePath, $rendered + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    $rendered
    if (-not $passed) {
        exit 1
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedTemp = [IO.Path]::GetFullPath($tempRoot)
        $systemTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
        if (-not $resolvedTemp.StartsWith($systemTemp, [StringComparison]::OrdinalIgnoreCase)) {
            throw "refusing to remove a path outside the system temp directory: $resolvedTemp"
        }
        Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
    }
}
