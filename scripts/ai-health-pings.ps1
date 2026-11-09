# Both pings are strictly read-only and independent. Neither ping can start a model or a service.
[CmdletBinding()]
param([ValidateSet('Status')][string]$Action='Status')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$taskName='EZStudioLab Assistant Local AI'
$expectedExe='H:\EZStudioLab_assistant\runtime\ai\bin\llama-server.exe'
function Test-Tcp([int]$port){
    try {
        $client=[Net.Sockets.TcpClient]::new()
        try {
            $async=$client.BeginConnect('127.0.0.1',$port,$null,$null)
            if(-not $async.AsyncWaitHandle.WaitOne(1500)){return $false}
            $client.EndConnect($async)
            return $true
        } finally { $client.Close() }
    } catch {return $false}
}
function Get-Http([string]$url){
    try {
        $value=Invoke-RestMethod -Uri $url -TimeoutSec 4 -ErrorAction Stop
        return @{collected=$true;value=$value;error=$null}
    } catch {
        return @{collected=$false;value=$null;error=$_.Exception.GetType().Name}
    }
}
$taskState='UNKNOWN'
$taskIdentity=$false
$taskError=$null
try {
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $taskState=[string]$task.State
    $actions=@($task.Actions)
    if($actions.Count -eq 1) {
        $args=[string]$actions[0].Arguments
        $taskIdentity=([string]$actions[0].Execute -ieq $expectedExe -and
            $args -match '(?i)(?:^|\s)-dev\s+Vulkan1(?:\s|$)' -and
            $args -match '(?i)(?:^|\s)-ngl\s+99(?:\s|$)' -and
            $args -match '(?i)(?:^|\s)--port\s+8720(?:\s|$)')
    }
} catch {$taskError=$_.Exception.GetType().Name}
$webUiTcp=Test-Tcp 8712
$webTcp=Test-Tcp 8713
$aiTcp=Test-Tcp 8720
$hard=[ordered]@{
    classification='HARD';collected=$true;timestamp_utc=[DateTime]::UtcNow.ToString('o')
    web_ui_tcp_8712=$webUiTcp;web_api_tcp_8713=$webTcp;llama_tcp_8720=$aiTcp
    gpu_task_state=$taskState;gpu_task_identity_valid=$taskIdentity
    state=$(if($webUiTcp -and $webTcp -and $aiTcp -and $taskIdentity -and $taskState -eq 'Running'){'OK'}else{'DEGRADED'})
    collection_error=$taskError
}
$web=Get-Http 'http://127.0.0.1:8713/api/health'
$ai=Get-Http 'http://127.0.0.1:8720/health'
$inference=Get-Http 'http://127.0.0.1:8713/api/inference/status'
$softOk=($web.collected -and $web.value.ok -eq $true -and $web.value.service -eq 'EZStudioLab Assistant' -and
    $ai.collected -and $ai.value.status -eq 'ok' -and $inference.collected -and
    $inference.value.ok -eq $true -and $inference.value.state -eq 'READY')
$soft=[ordered]@{
    classification='SOFT';timestamp_utc=[DateTime]::UtcNow.ToString('o')
    state=$(if($softOk){'OK'}elseif(-not $web.collected -or -not $ai.collected -or -not $inference.collected){'COLLECTION_ERROR'}else{'DEGRADED'})
    web_api_health=$($web.collected -and $web.value.ok -eq $true -and $web.value.service -eq 'EZStudioLab Assistant')
    llama_api_health=$($ai.collected -and $ai.value.status -eq 'ok')
    inference_ready=$($inference.collected -and $inference.value.state -eq 'READY')
    web_version=$(if($web.collected){[string]$web.value.version}else{$null})
    errors=@(@($web.error,$ai.error,$inference.error) | Where-Object {$_})
}
[pscustomobject]@{schema='ezstudio.assistant.pings.v1';hard=$hard;soft=$soft} | ConvertTo-Json -Depth 6
# Health observation is not a mutation. Failure does not trigger a start/stop.
