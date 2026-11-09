# One-shot Assistant dependency startup; no supervisor loop and no lifecycle changes to FrankenPHP.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskName = 'EZStudioLab Assistant Local AI'
$intentFile = 'H:\EZStudioLab_assistant\runtime\state\assistant-local-ai-intent.json'
$pingScript = 'H:\EZStudioLab_assistant\scripts\ai-health-pings.ps1'
$expectedExe = 'H:\EZStudioLab_assistant\runtime\ai\bin\llama-server.exe'
$logDir = 'H:\EZStudioLab_assistant\runtime\state'
$logFile = Join-Path $logDir 'ai-auto-bootstrap.log'
function Log([string]$message) {
    if(-not (Test-Path -LiteralPath $logDir -PathType Container)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -LiteralPath $logFile -Encoding UTF8 -Value ((Get-Date).ToUniversalTime().ToString('o') + ' ' + $message)
}
function Test-Llama {
    try {
        $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8720/health' -TimeoutSec 2 -ErrorAction Stop
        return ($r.status -eq 'ok')
    } catch {return $false}
}
function Get-GpuTask {
    $t=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $actions=@($t.Actions)
    if($actions.Count -ne 1){throw 'GPU_TASK_ACTION_COUNT_INVALID'}
    $a=$actions[0]
    if(-not [string]::Equals([string]$a.Execute,$expectedExe,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'GPU_TASK_EXECUTABLE_MISMATCH'
    }
    $args=[string]$a.Arguments
    foreach($pattern in @('(?i)(?:^|\s)-dev\s+Vulkan1(?:\s|$)',
                         '(?i)(?:^|\s)-ngl\s+99(?:\s|$)',
                         '(?i)(?:^|\s)-c\s+4096(?:\s|$)',
                         '(?i)(?:^|\s)--host\s+127\.0\.0\.1(?:\s|$)',
                         '(?i)(?:^|\s)--port\s+8720(?:\s|$)')) {
        if($args -notmatch $pattern){throw 'GPU_TASK_ARGUMENTS_MISMATCH'}
    }
    if($args -notmatch '(?i)(?:^|\s)-m\s+"?H:\\EZStudioLab_assistant\\runtime\\models-cache\\assistant\\bench\\') {
        throw 'GPU_TASK_MODEL_PATH_MISMATCH'
    }
    return $t
}
try {
    # FrankenPHP is shared. Never attempt to start or modify it here.
    $webService=Get-Service -Name 'EZS_FrankenPHP' -ErrorAction Stop
    if($webService.Status -ne 'Running') {Log 'SKIP_WEB_SERVICE_NOT_RUNNING';exit 0}
    $webReady=$false
    for($i=0;$i -lt 30;$i++) {
        try {
            $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8713/api/health' -TimeoutSec 3 -ErrorAction Stop
            if($r.ok -eq $true -and $r.service -eq 'EZStudioLab Assistant'){$webReady=$true;break}
        } catch {}
        Start-Sleep -Seconds 2
    }
    if(-not $webReady) {Log 'SKIP_ASSISTANT_WEB_NOT_AVAILABLE';exit 0}
    if(Test-Path -LiteralPath $intentFile -PathType Leaf) {
        $intent=Get-Content -LiteralPath $intentFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if($intent.schema -ne 'ezstudio.assistant.local-ai-intent.v1' -or $intent.state -notin @('RUNNING','STOPPED')) {throw 'AI_INTENT_INVALID'}
        if($intent.state -eq 'STOPPED') {Log 'SKIP_EXPLICIT_STOPPED';exit 0}
    }
    $task=Get-GpuTask
    if(Test-Llama) {
        & $pingScript -Action Status | Out-Null
        if($LASTEXITCODE -ne 0){throw 'PING_COLLECTION_FAILED'}
        Log 'ALREADY_READY_8720';exit 0
    }
    if($task.State -eq 'Running') {
        # Existing launch may still load its model; do not launch a duplicate.
        Log 'GPU_TASK_ALREADY_RUNNING_WAITING_FOR_HEALTH'
    } elseif($task.State -eq 'Ready') {
        $listeners=@(Get-NetTCPConnection -LocalPort 8720 -State Listen -ErrorAction SilentlyContinue)
        if($listeners.Count -gt 0) {throw 'PORT_8720_OCCUPIED_UNHEALTHY_REFUSED'}
        Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
        Log 'GPU_TASK_START_REQUESTED'
    } else {throw ('GPU_TASK_STATE_INVALID_'+$task.State)}
    for($i=0;$i -lt 45;$i++) {
        if(Test-Llama) {
            & $pingScript -Action Status | Out-Null
            if($LASTEXITCODE -ne 0){throw 'PING_COLLECTION_FAILED'}
            Log 'GPU_READY_8720';exit 0
        }
        if((Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State -eq 'Ready') {
            throw 'GPU_TASK_EXITED_BEFORE_READY'
        }
        Start-Sleep -Seconds 2
    }
    throw 'GPU_READY_TIMEOUT'
} catch {
    Log ('BOOTSTRAP_FAILED '+$_.Exception.Message)
    exit 2
}
