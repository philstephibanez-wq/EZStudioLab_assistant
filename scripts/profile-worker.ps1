# Lifecycle of the PROFILE worker exclusively. Does not manage web or Qwen.
param([ValidateSet('start','stop','restart','status','install-task')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskName='EZStudioLab Assistant PROFILE IA Requests'
$supervisor=Join-Path $root 'app\profile_worker_supervisor.py'
$worker=Join-Path $root 'runtime\profile_ai_requests_worker.py'
$python='C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
function Get-ProfileProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and (
      $_.CommandLine.IndexOf($worker,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or
      $_.CommandLine.IndexOf($supervisor,[StringComparison]::OrdinalIgnoreCase) -ge 0
    )
  })
}
function Wait-Zero([int]$seconds=15) {
  $end=[DateTime]::UtcNow.AddSeconds($seconds)
  while ([DateTime]::UtcNow -lt $end) {
    if (@(Get-ProfileProcesses).Count -eq 0) { return }
    Start-Sleep -Milliseconds 300
  }
  throw 'PROFILE_WORKER_STOP_INCOMPLETE'
}
function Confirm-Task {
  $t=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
  $a=@($t.Actions)
  if ($a.Count -ne 1) { throw 'PROFILE_TASK_ACTION_COUNT_INVALID' }
  return $t
}
function Assert-Orchestrator-Idle {
  # Read-only preflight. This is NOT an atomic claim/lease or maintenance lock.
  $url='http://EZSTUDIO-MAIN:8700/api/jobs'
  try {
    $response=Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 5 -ErrorAction Stop
  } catch {
    throw "PROFILE_ORCHESTRATOR_UNREACHABLE:$($_.Exception.Message)"
  }
  if ($null -eq $response -or $response.ok -ne $true -or $null -eq $response.jobs) {
    throw 'PROFILE_ORCHESTRATOR_STATUS_INVALID'
  }
  if ($null -eq $response.queue_errors) { throw 'PROFILE_ORCHESTRATOR_QUEUE_HEALTH_UNKNOWN' }
  if ($response.queue_errors.PSObject.Properties.Name -contains 'lab_ai') {
    throw 'PROFILE_ORCHESTRATOR_LAB_AI_QUEUE_UNREADABLE'
  }
  if ($null -eq $response.ai_canonical_count -or [int]$response.ai_canonical_count -le 0) {
    throw 'PROFILE_ORCHESTRATOR_AI_HISTORY_UNAVAILABLE'
  }
  $active=@($response.jobs | Where-Object {
    $_.kind -eq 'assistant.profile.review' -and
    ([string]$_.state).ToLowerInvariant() -in @('running','claimed','cancelling')
  })
  if ($active.Count -gt 0) {
    throw "PROFILE_ORCHESTRATOR_JOB_ACTIVE:count=$($active.Count)"
  }
  Write-Output 'PROFILE_ORCHESTRATOR_READONLY_IDLE_OK (NOT_ATOMIC)'
}
function Get-RelayMaintenance([string]$mode) {
  $base=[string]$env:EZS_R2E_RELAY_URL
  $token=[string]$env:EZS_R2E_RELAY_TOKEN
  if ([string]::IsNullOrWhiteSpace($base) -or [string]::IsNullOrWhiteSpace($token)) {
    throw 'PROFILE_R2E_MAINTENANCE_CONFIG_REQUIRED'
  }
  $path='/r2e/profile/maintenance'
  if ($mode -ne 'status') { $path += ('/' + $mode) }
  $method=if ($mode -eq 'status') { 'GET' } else { 'POST' }
  try {
    $v=Invoke-RestMethod -Uri ($base.TrimEnd('/')+$path) -Method $method -Headers @{'X-EZS-R2E-Token'=$token} -TimeoutSec 6
  } catch { throw "PROFILE_R2E_MAINTENANCE_UNREACHABLE:$($_.Exception.Message)" }
  if ($v.ok -ne $true) { throw 'PROFILE_R2E_MAINTENANCE_INVALID_RESPONSE' }
  return $v
}
function Stop-Profile {
  if ($env:EZS_PROFILE_MAINTENANCE_STOP -ne 'I_CONFIRMED_NO_ACTIVE_JOB') {
    throw 'PROFILE_STOP_REQUIRES_CONFIRMED_IDLE_JOB'
  }
  $pause=Get-RelayMaintenance 'pause'
  if ($pause.maintenance -ne $true -or $pause.active -ne $false) { throw 'PROFILE_R2E_JOB_ACTIVE_OR_PAUSE_FAILED' }
  Assert-Orchestrator-Idle
  $t=Confirm-Task
  if ($t.State -eq 'Running') { Stop-ScheduledTask -TaskName $taskName }
  Start-Sleep -Milliseconds 350
  $check=Get-RelayMaintenance 'status'
  if ($check.maintenance -ne $true -or $check.active -ne $false) { throw 'PROFILE_R2E_JOB_ACTIVE_DURING_STOP' }
  Assert-Orchestrator-Idle
  $live=@(Get-ProfileProcesses)
  # Only a targeted stop, never kill all python processes.
  foreach ($p in $live) {
    $now=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ProcessId)"
    if ($null -eq $now -or $now.CreationDate -ne $p.CreationDate -or
        -not $now.CommandLine -or
        ($now.CommandLine.IndexOf($worker,[StringComparison]::OrdinalIgnoreCase) -lt 0 -and
         $now.CommandLine.IndexOf($supervisor,[StringComparison]::OrdinalIgnoreCase) -lt 0)) {
      throw "PROFILE_PID_CHANGED:$($p.ProcessId)"
    }
    Stop-Process -Id $p.ProcessId -ErrorAction Stop
  }
  Wait-Zero
  Write-Output 'PROFILE_WORKER_STOP_OK count=0'
}
function Start-Profile {
  $t=Confirm-Task
  $a=@($t.Actions)[0]
  if ($a.Execute -notmatch '(?i)python(?:w)?\.exe$' -or $a.Arguments -notmatch 'profile_worker_supervisor\.py') {
    throw 'PROFILE_TASK_NOT_SUPERVISED:install-task required'
  }
  $live=@(Get-ProfileProcesses)
  if ($live.Count -eq 2 -and @($live | Where-Object { $_.CommandLine.IndexOf($supervisor,[StringComparison]::OrdinalIgnoreCase) -ge 0 }).Count -eq 1 -and @($live | Where-Object { $_.CommandLine.IndexOf($worker,[StringComparison]::OrdinalIgnoreCase) -ge 0 }).Count -eq 1) { $check=Get-RelayMaintenance 'status'; if ($check.maintenance -eq $true) { [void](Get-RelayMaintenance 'resume') }; Write-Output "PROFILE_WORKER_ALREADY_RUNNING supervisor=1 worker=1"; return }
  if ($live.Count -ne 0) { throw "PROFILE_WORKER_UNMANAGED_OR_DUPLICATE_PROCESSES count=$($live.Count)" }
  Start-ScheduledTask -TaskName $taskName
  Start-Sleep -Seconds 2
  $live=@(Get-ProfileProcesses)
  if ($live.Count -ne 2) { throw "PROFILE_WORKER_START_INCOMPLETE processes=$($live.Count)" }
  $check=Get-RelayMaintenance 'status'
  if ($check.maintenance -eq $true) { [void](Get-RelayMaintenance 'resume') }
  Write-Output 'PROFILE_WORKER_START_OK supervisor=1 worker=1'
}
if ($Action -eq 'status') {
  $t=Confirm-Task
  $live=@(Get-ProfileProcesses)
  $live | Select-Object ProcessId,Name,CreationDate,CommandLine | Format-List
  Write-Output "PROFILE_WORKER_STATUS count=$($live.Count) task=$($t.State)"
  if ($live.Count -ne 0 -and $live.Count -ne 2) { exit 3 }
} elseif ($Action -eq 'install-task') {
  # Deliberately fail rather than overwrite unknown scheduler configurations.
  $t=Confirm-Task
  $a=@($t.Actions)[0]
  if ($a.Execute -notmatch '(?i)wscript\.exe$' -or $a.Arguments -notmatch 'profile-ai-hidden\.vbs') {
    throw 'PROFILE_TASK_UNEXPECTED_LEGACY_ACTION'
  }
  if (@(Get-ProfileProcesses).Count -gt 0) { throw 'PROFILE_TASK_INSTALL_REQUIRES_WORKER_STOPPED' }
  if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PROFILE_PYTHON_MISSING' }
  if (-not (Test-Path -LiteralPath $worker -PathType Leaf)) { throw 'PROFILE_WORKER_MISSING' }
  $taskExecAction=New-ScheduledTaskAction -Execute $python -Argument ('-u "' + $supervisor + '"') -WorkingDirectory $root
  Set-ScheduledTask -TaskName $taskName -Action $taskExecAction | Out-Null
  Write-Output 'PROFILE_TASK_SUPERVISOR_INSTALLED'
} elseif ($Action -eq 'start') {
  Start-Profile
} elseif ($Action -eq 'stop') {
  Stop-Profile
} else {
  Stop-Profile
  Start-Profile
}
