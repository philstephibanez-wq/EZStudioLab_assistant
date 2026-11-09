# The Assistant owns a one-shot task that reacts to FrankenPHP service start and user logon.
# It launches the EXISTING Vulkan Llama scheduled task; never manages FrankenPHP.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','Install','Status','Remove')][string]$Action)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='H:\EZStudioLab_assistant'
$taskName='EZStudioLab Assistant AI Bootstrap'
$gpuTask='EZStudioLab Assistant Local AI'
$bootstrap=Join-Path $root 'scripts\ai-auto-bootstrap.ps1'
$owner=[Security.Principal.WindowsIdentity]::GetCurrent().Name
function Assert-InstallReady {
    if(-not (Test-Path -LiteralPath $bootstrap -PathType Leaf)){throw 'BOOTSTRAP_SCRIPT_MISSING'}
    $gpu=Get-ScheduledTask -TaskName $gpuTask -ErrorAction Stop
    if(@($gpu.Actions).Count -ne 1){throw 'GPU_TASK_ACTION_INVALID'}
    if([string]$gpu.Actions[0].Execute -ine 'H:\EZStudioLab_assistant\runtime\ai\bin\llama-server.exe') {
        throw 'GPU_TASK_EXECUTABLE_MISMATCH'
    }
    $args=[string]$gpu.Actions[0].Arguments
    if($args -notmatch '(?i)(?:^|\s)-dev\s+Vulkan1(?:\s|$)') {throw 'GPU_TASK_NOT_VULKAN'}
}
function Get-BootstrapTask {
    return Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
}
if($Action -eq 'Preflight') {
    Assert-InstallReady
    if($null -ne (Get-BootstrapTask)){throw 'BOOTSTRAP_TASK_EXISTS_REFUSED'}
    Write-Host 'ASSISTANT_AUTOSTART_PREFLIGHT_OK'
    exit 0
}
if($Action -eq 'Status') {
    $task=Get-BootstrapTask
    if($null -eq $task){Write-Host 'ASSISTANT_AUTOSTART_NOT_INSTALLED';exit 0}
    Write-Host ('ASSISTANT_AUTOSTART_TASK_STATE='+$task.State)
    Write-Host ('ASSISTANT_AUTOSTART_TRIGGER_COUNT='+@($task.Triggers).Count)
    exit 0
}
if($Action -eq 'Remove') {
    $task=Get-BootstrapTask
    if($null -eq $task){Write-Host 'ASSISTANT_AUTOSTART_ALREADY_ABSENT';exit 0}
    if([string]$task.Actions[0].Execute -notmatch '(?i)\\powershell\.exe$' -or
       [string]$task.Actions[0].Arguments -notlike ('*'+$bootstrap+'*')) {
        throw 'BOOTSTRAP_TASK_IDENTITY_MISMATCH'
    }
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    Write-Host 'ASSISTANT_AUTOSTART_REMOVED_NO_GPU_ACTION'
    exit 0
}
Assert-InstallReady
if($null -ne (Get-BootstrapTask)){throw 'BOOTSTRAP_TASK_EXISTS_REFUSED'}
# Register-ScheduledTask does not expose an EventTrigger constructor in PowerShell 5.1.
# The XML uses Task Scheduler 1.3's native EventTrigger plus a LogonTrigger catch-up.
# Event 7036: Service Control Manager, service status transition. Query checks only
# the service name, because localized event state strings differ on French Windows.
$subscription="<QueryList><Query Id='0' Path='System'><Select Path='System'>*[System[Provider[@Name='Service Control Manager'] and (EventID=7036)]] and *[EventData[(Data[@Name='param1']='EZS_FrankenPHP' or Data[@Name='param1']='EZS FrankenPHP')]]</Select></Query></QueryList>"
$escapedSub=[Security.SecurityElement]::Escape($subscription)
$escapedUser=[Security.SecurityElement]::Escape($owner)
$escapedScript=[Security.SecurityElement]::Escape($bootstrap)
$escapedRoot=[Security.SecurityElement]::Escape($root)
$xml=@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Assistant-owned one-shot bootstrap of the existing Vulkan Llama task; no service lifecycle mutation</Description></RegistrationInfo>
  <Triggers>
    <EventTrigger><Enabled>true</Enabled><Subscription>$escapedSub</Subscription><Delay>PT15S</Delay></EventTrigger>
    <LogonTrigger><Enabled>true</Enabled><UserId>$escapedUser</UserId><Delay>PT20S</Delay></LogonTrigger>
  </Triggers>
  <Principals><Principal id="Author"><UserId>$escapedUser</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle><ExecutionTimeLimit>PT4M</ExecutionTimeLimit><Priority>7</Priority>
  </Settings>
  <Actions Context="Author"><Exec><Command>C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe</Command><Arguments>-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$escapedScript"</Arguments><WorkingDirectory>$escapedRoot</WorkingDirectory></Exec></Actions>
</Task>
"@
# Task Scheduler API requires UTF-16 XML input; this does not write any UTF-16 file.
$created=$false
try {
    Register-ScheduledTask -TaskName $taskName -Xml $xml -ErrorAction Stop | Out-Null
    $created=$true
    $task=Get-BootstrapTask
    if($null -eq $task -or @($task.Triggers).Count -ne 2){throw 'BOOTSTRAP_REGISTRATION_UNVERIFIED'}
    Write-Host 'ASSISTANT_AUTOSTART_INSTALLED_EVENTS_AND_LOGON'
} catch {
    if($created){Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue}
    throw
}
