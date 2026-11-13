[CmdletBinding()]
param(
    [ValidateSet('Check','Install','Update','Status','Disable','Uninstall')]
    [string]$Mode = 'Check',
    [string]$ApprovalReference
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$policyPath = Join-Path $repoRoot 'docs\zero-trust\scheduled-validation-policy.yaml'
$policy = Get-Content -Raw -LiteralPath $policyPath | ConvertFrom-Json
$taskName = [string]$policy.scheduler.task_name
$taskPath = [string]$policy.scheduler.task_path
$runtimeRoot = Join-Path $repoRoot '.runtime\zero-trust\scheduled-validation'
$python = (Get-Command python -ErrorAction Stop).Source
$runner = Join-Path $repoRoot 'tools\continuous_verification\run_scheduled_validation.py'
$wrapper = Join-Path $repoRoot 'tools\live-validation\run-scheduled-validation.ps1'

function Get-ConfiguredTask {
    Get-ScheduledTask -TaskName $taskName -TaskPath $taskPath -ErrorAction SilentlyContinue
}

function Assert-Approval([string]$Operation) {
    $expected = "^USER_APPROVED_ZT_SCH_001_${Operation}_[A-Za-z0-9._-]+$"
    if (-not $ApprovalReference -or $ApprovalReference -notmatch $expected) {
        throw "$Operation requires an explicit bounded approval reference matching $expected"
    }
}

function Get-ScheduleFingerprint {
    $output = & $python $runner --check
    if ($LASTEXITCODE -ne 0) { throw 'ZT-SCH-001 configuration check failed.' }
    $match = [regex]::Match(($output -join "`n"), 'schedule_fingerprint=([0-9a-f]{64})')
    if (-not $match.Success) { throw 'Schedule fingerprint was not produced.' }
    $match.Groups[1].Value
}

function New-FixedTaskSettings {
    New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds ([int]$policy.runtime_controls.timeout_seconds)) -RestartCount 0 -StartWhenAvailable:$([bool]$policy.trigger.start_when_available) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
}

function Assert-TaskDefinition($Task, [switch]$AllowDisabledCatchUp) {
    if (-not $Task) { throw 'The scheduled task is not installed.' }
    if ($Task.Actions.Count -ne 1 -or $Task.Triggers.Count -ne 1) { throw 'Task action/trigger count differs from the fixed definition.' }
    $action = $Task.Actions[0]
    $expectedArguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$wrapper`" -Mode ExecuteReadOnly"
    if ([IO.Path]::GetFileName([string]$action.Execute) -ne 'powershell.exe' -or [string]$action.Arguments -ne $expectedArguments -or [string]$action.WorkingDirectory -ne $repoRoot) { throw 'Task action differs from the fixed wrapper.' }
    $trigger = $Task.Triggers[0]
    if ([int]$trigger.DaysInterval -ne 1) { throw 'Task trigger is not daily.' }
    $start = [datetimeoffset]::Parse([string]$trigger.StartBoundary)
    if ($start.TimeOfDay.ToString('hh\:mm\:ss') -ne [string]$policy.trigger.daily_start_time_local) { throw 'Task start time differs from the fixed policy.' }
    $actualCatchUp = [bool]$Task.Settings.StartWhenAvailable
    $expectedCatchUp = [bool]$policy.trigger.start_when_available
    $legacyCatchUp = $AllowDisabledCatchUp -and $expectedCatchUp -and -not $actualCatchUp
    if ([string]$Task.Settings.MultipleInstances -notin @('IgnoreNew','2') -or ($actualCatchUp -ne $expectedCatchUp -and -not $legacyCatchUp)) { throw 'Task overlap/catch-up settings differ from policy.' }
    if ([string]$Task.Principal.LogonType -notin @('Interactive','InteractiveToken','3') -or [string]$Task.Principal.RunLevel -notin @('Limited','0')) { throw 'Task principal is not limited interactive-token.' }
}

function Write-Status($Task) {
    Assert-TaskDefinition $Task
    $info = Get-ScheduledTaskInfo -TaskName $taskName -TaskPath $taskPath
    $status = [ordered]@{
        package_id = 'ZT-SCH-001'
        schedule_id = [string]$policy.metadata.schedule_id
        task_name = $taskName
        task_path = $taskPath
        captured_at = [datetime]::UtcNow.ToString('o')
        state = [string]$Task.State
        enabled = [bool]$Task.Settings.Enabled
        last_run_time = if ([int64]$info.LastTaskResult -eq 267011) { $null } elseif ($info.LastRunTime -gt [datetime]::MinValue) { $info.LastRunTime.ToUniversalTime().ToString('o') } else { $null }
        next_run_time = if ($info.NextRunTime -gt [datetime]::MinValue) { $info.NextRunTime.ToUniversalTime().ToString('o') } else { $null }
        last_task_result = [int64]$info.LastTaskResult
        definition_status = 'MATCHED'
        schedule_fingerprint = Get-ScheduleFingerprint
        account_value_recorded = $false
        credential_stored = $false
    }
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    $status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runtimeRoot 'scheduler-status.json') -Encoding utf8
    $status
}

switch ($Mode) {
    'Check' {
        & $python $runner --check
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $task = Get-ConfiguredTask
        if ($task) { Assert-TaskDefinition $task; Write-Output '[PASS] ZT-SCH-001 task is installed and matches the fixed definition.' }
        else { Write-Output '[PASS] ZT-SCH-001 preparation is valid and the task is not installed.' }
    }
    'Install' {
        Assert-Approval 'INSTALL'
        & $python $runner --check
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $task = Get-ConfiguredTask
        if ($task) {
            Assert-TaskDefinition $task
        } else {
            $startAt = [datetime]::Today.Add([timespan]::Parse([string]$policy.trigger.daily_start_time_local))
            $arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$wrapper`" -Mode ExecuteReadOnly"
            $action = New-ScheduledTaskAction -Execute (Get-Command powershell).Source -Argument $arguments -WorkingDirectory $repoRoot
            $trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 1 -At $startAt
            $settings = New-FixedTaskSettings
            $principalId = [Security.Principal.WindowsIdentity]::GetCurrent().Name
            $principal = New-ScheduledTaskPrincipal -UserId $principalId -LogonType Interactive -RunLevel Limited
            $definition = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'ZT-SCH-001 bounded daily read-only validation; no retry, remediation, or infrastructure mutation.'
            Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath -InputObject $definition | Out-Null
            $task = Get-ConfiguredTask
        }
        Assert-TaskDefinition $task
        $info = Get-ScheduledTaskInfo -TaskName $taskName -TaskPath $taskPath
        $registration = [ordered]@{
            package_id = 'ZT-SCH-001'
            schedule_id = [string]$policy.metadata.schedule_id
            installed_at = [datetime]::UtcNow.ToString('o')
            first_scheduled_run = $info.NextRunTime.ToUniversalTime().ToString('o')
            task_name = $taskName
            task_path = $taskPath
            schedule_fingerprint = Get-ScheduleFingerprint
            approval_reference = $ApprovalReference
            credential_stored = $false
            infrastructure_mutation_authorized = $false
            automatic_retry = $false
            authoritative_update_performed = $false
        }
        New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
        $registration | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runtimeRoot 'registration.json') -Encoding utf8
        Write-Status $task | Out-Null
        Write-Output '[PASS] ZT-SCH-001 daily task installed with the fixed limited interactive-token definition.'
    }
    'Update' {
        Assert-Approval 'UPDATE'
        & $python $runner --check
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $task = Get-ConfiguredTask
        Assert-TaskDefinition $task -AllowDisabledCatchUp
        if ([bool]$task.Settings.StartWhenAvailable -ne [bool]$policy.trigger.start_when_available) {
            Set-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Settings (New-FixedTaskSettings) | Out-Null
        }
        $task = Get-ConfiguredTask
        Assert-TaskDefinition $task
        $status = Write-Status $task
        $update = [ordered]@{
            package_id = 'ZT-SCH-001'
            schedule_id = [string]$policy.metadata.schedule_id
            updated_at = [datetime]::UtcNow.ToString('o')
            operation = 'BOUNDED_CATCH_UP_UPDATE'
            approval_reference = $ApprovalReference
            definition_status = 'MATCHED'
            schedule_fingerprint = Get-ScheduleFingerprint
            start_when_available = [bool]$task.Settings.StartWhenAvailable
            catch_up_window = [string]$policy.trigger.catch_up_window
            next_run_time = $status.next_run_time
            credential_stored = $false
            live_validator_started = $false
            authoritative_update_performed = $false
        }
        $updateRoot = Join-Path $runtimeRoot 'updates'
        New-Item -ItemType Directory -Path $updateRoot -Force | Out-Null
        $updateName = 'update-{0}.json' -f [datetime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
        $update | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $updateRoot $updateName) -Encoding utf8
        Write-Output '[PASS] ZT-SCH-001 task updated to the bounded two-hour catch-up definition; no live validator was started.'
    }
    'Status' {
        $task = Get-ConfiguredTask
        $status = Write-Status $task
        Write-Output ("[PASS] task={0} state={1} enabled={2} last_result={3}" -f $taskName,$status.state,$status.enabled,$status.last_task_result)
    }
    'Disable' {
        Assert-Approval 'DISABLE'
        $task = Get-ConfiguredTask
        Assert-TaskDefinition $task
        Disable-ScheduledTask -TaskName $taskName -TaskPath $taskPath | Out-Null
        Write-Status (Get-ConfiguredTask) | Out-Null
        Write-Output '[PASS] ZT-SCH-001 task disabled; runtime evidence was preserved.'
    }
    'Uninstall' {
        Assert-Approval 'UNINSTALL'
        $task = Get-ConfiguredTask
        Assert-TaskDefinition $task
        Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false
        Write-Output '[PASS] ZT-SCH-001 task removed; runtime evidence was preserved.'
    }
}
