[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','Status','Start','Stop')][string]$Action)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='H:\EZStudioLab_assistant'
$exe=Join-Path $root 'runtime\ai\bin\llama-server.exe'
$model=Join-Path $root 'runtime\models-cache\assistant\bench\qwen2.5-1.5b-instruct-q4_k_m\qwen2.5-1.5b-instruct-q4_k_m.gguf'
$taskName='EZStudioLab Assistant Local AI'
$intentFile=Join-Path $root 'runtime\state\assistant-local-ai-intent.json'
$port=8720
function Get-Intent {
    if(-not (Test-Path -LiteralPath $intentFile -PathType Leaf)){return 'UNKNOWN'}
    $raw=Get-Content -LiteralPath $intentFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if($raw.schema -ne 'ezstudio.assistant.local-ai-intent.v1' -or $raw.state -notin @('RUNNING','STOPPED')){
        throw 'ASSISTANT_INTENT_INVALID'
    }
    return [string]$raw.state
}
function Set-Intent([string]$state){
    if($state -notin @('RUNNING','STOPPED')){throw 'ASSISTANT_INTENT_VALUE_INVALID'}
    $dir=Split-Path -Parent $intentFile
    if(-not (Test-Path -LiteralPath $dir -PathType Container)){New-Item -ItemType Directory -Path $dir -Force | Out-Null}
    $body=([ordered]@{schema='ezstudio.assistant.local-ai-intent.v1';state=$state;updated_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress)
    $temp=Join-Path $dir ([IO.Path]::GetRandomFileName()+'.json')
    [IO.File]::WriteAllText($temp,$body,[Text.UTF8Encoding]::new($false))
    try {Move-Item -LiteralPath $temp -Destination $intentFile -Force -ErrorAction Stop}
    finally {if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}
}
function Get-Task {
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $actions=@($task.Actions)
    if($actions.Count -ne 1){throw 'ASSISTANT_TASK_ACTION_COUNT_INVALID'}
    $a=$actions[0]
    if(-not [string]::Equals([string]$a.Execute,$exe,[StringComparison]::OrdinalIgnoreCase)){
        throw 'ASSISTANT_TASK_EXECUTABLE_MISMATCH'
    }
    $args=[string]$a.Arguments
    $quoted=[regex]::Escape($model)
    if($args -notmatch ('(?i)(?:^|\s)-m\s+"?'+$quoted+'"?(?:\s|$)') -or
       $args -notmatch '(?i)(?:^|\s)-dev\s+Vulkan1(?:\s|$)' -or
       $args -notmatch '(?i)(?:^|\s)-ngl\s+99(?:\s|$)' -or
       $args -notmatch '(?i)(?:^|\s)-c\s+4096(?:\s|$)' -or
       $args -notmatch '(?i)(?:^|\s)--host\s+127\.0\.0\.1(?:\s|$)' -or
       $args -notmatch '(?i)(?:^|\s)--port\s+8720(?:\s|$)'){
        throw 'ASSISTANT_TASK_GPU_ARGUMENTS_MISMATCH'
    }
    if($task.State -notin @('Ready','Running')){throw ('ASSISTANT_TASK_STATE_UNEXPECTED_'+$task.State)}
    return $task
}
function Get-Listener {
    $connections=@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    $owners=@($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    if($owners.Count -gt 1){throw 'ASSISTANT_LLAMA_MULTIPLE_PORT_OWNERS'}
    if($owners.Count -eq 0){return $null}
    if([int]$owners[0] -le 0){throw 'ASSISTANT_LLAMA_UNKNOWN_PORT_OWNER'}
    return [int]$owners[0]
}
function Assert-Owned([int]$ownerPid){
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction Stop
    if($null -eq $p){throw 'ASSISTANT_LLAMA_PID_MISSING'}
    if(-not [string]::Equals([string]$p.ExecutablePath,$exe,[StringComparison]::OrdinalIgnoreCase)){
        throw 'ASSISTANT_LLAMA_FOREIGN_EXECUTABLE'
    }
    $cmd=[string]$p.CommandLine
    if($cmd -notmatch '(?i)(?:^|\s)-dev\s+Vulkan1(?:\s|$)' -or
       $cmd -notmatch '(?i)(?:^|\s)--port\s+8720(?:\s|$)' -or
       $cmd.IndexOf($model,[StringComparison]::OrdinalIgnoreCase) -lt 0){
        throw 'ASSISTANT_LLAMA_FOREIGN_ARGUMENTS'
    }
}
function Test-Health {
    try {
        $response=Invoke-RestMethod -Uri 'http://127.0.0.1:8720/health' -TimeoutSec 3 -ErrorAction Stop
        return $response.status -eq 'ok'
    } catch {return $false}
}
function Preflight {
    if(-not (Test-Path -LiteralPath $exe -PathType Leaf)){throw 'ASSISTANT_GPU_BINARY_MISSING'}
    if(-not (Test-Path -LiteralPath $model -PathType Leaf)){throw 'ASSISTANT_GPU_MODEL_MISSING'}
    $null=Get-Task
    $owner=Get-Listener
    if($null -ne $owner){Assert-Owned $owner}
    Write-Output 'ASSISTANT_GPU_LIFECYCLE_PREFLIGHT_OK'
}
if($Action -eq 'Preflight'){Preflight;exit 0}
if($Action -eq 'Status'){
    $task=Get-Task
    $intent=Get-Intent
    $owner=Get-Listener
    if($null -ne $owner){Assert-Owned $owner}
    $healthy=($null -ne $owner -and (Test-Health))
    Write-Output ('ASSISTANT_INTENT='+$intent)
    Write-Output ('ASSISTANT_TASK_STATE='+$task.State)
    Write-Output ('ASSISTANT_LLAMA_PID='+$(if($null -ne $owner){$owner}else{'NONE'}))
    Write-Output ('ASSISTANT_LLAMA_HEALTH='+$(if($healthy){'READY'}else{'UNAVAILABLE'}))
    Write-Output 'ASSISTANT_GPU_LIFECYCLE_STATUS_OK'
    exit 0
}
Preflight
if($Action -eq 'Start'){
    # Explicit START is the only operation allowed to change STOPPED to RUNNING.
    $task=Get-Task
    $owner=Get-Listener
    if($null -ne $owner){
        if($task.State -ne 'Running' -or -not (Test-Health)){throw 'ASSISTANT_LLAMA_EXISTING_NOT_READY'}
        Set-Intent 'RUNNING'
        Write-Output 'ASSISTANT_GPU_ALREADY_RUNNING_READY'
        exit 0
    }
    if($task.State -eq 'Running'){throw 'ASSISTANT_TASK_RUNNING_WITHOUT_LISTENER'}
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $ready=$false
    for($i=0;$i -lt 90;$i++){
        Start-Sleep -Seconds 1
        $owner=Get-Listener
        if($null -ne $owner){Assert-Owned $owner}
        if($null -ne $owner -and (Test-Health)){$ready=$true;break}
        $state=(Get-Task).State
        if($state -eq 'Ready'){break}
    }
    if(-not $ready){throw 'ASSISTANT_LLAMA_GPU_START_NOT_READY'}
    Set-Intent 'RUNNING'
    Write-Output 'ASSISTANT_GPU_STARTED_READY_8720'
    exit 0
}
if($Action -eq 'Stop'){
    $task=Get-Task
    $owner=Get-Listener
    if($null -ne $owner){Assert-Owned $owner}
    if($task.State -eq 'Running' -and $null -eq $owner){throw 'ASSISTANT_STOP_UNVERIFIED_RUNNING_TASK'}
    Set-Intent 'STOPPED'
    if($task.State -eq 'Running'){
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $done=$false
        for($i=0;$i -lt 30;$i++){
            Start-Sleep -Seconds 1
            $owner=Get-Listener
            if($null -eq $owner -and (Get-Task).State -eq 'Ready'){$done=$true;break}
            if($null -ne $owner){Assert-Owned $owner}
        }
        if(-not $done){throw 'ASSISTANT_GPU_STOP_NOT_ATTESTED'}
    }
    Write-Output 'ASSISTANT_GPU_STOPPED_INTENT_PERSISTED'
    exit 0
}
