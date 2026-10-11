param(
    [string]$Python = "python",
    [string]$NodeId = "EZStudioLab_assistant-$env:COMPUTERNAME",
    [Parameter(Mandatory=$true)][string]$SharedModelRoot,
    [string]$ModelCache = "$env:LOCALAPPDATA\EZStudioLab_assistant\models",
    [string]$HostRepo = "",
    [ValidateSet("capabilities","check-model","queue","watch","distributed-probe","distributed-watch","evaluate-gate")][string]$Mode = "capabilities",
    [string]$Model = "",
    [string]$BaseUrl = "",
    [string]$Token = "",
    [string]$GateReport = "",
    [double]$PollSeconds = 5.0,
    [int]$Iterations = 0,
    [int]$Limit = 100
)
$ErrorActionPreference = "Stop"
$assistantRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$app = Join-Path $assistantRoot "app\main.py"
if ([string]::IsNullOrWhiteSpace($HostRepo)) { $HostRepo = Split-Path -Parent $assistantRoot }
$pythonRoot = Join-Path $HostRepo "python"
if (-not (Test-Path -LiteralPath $app -PathType Leaf)) { throw "EZStudioLab_assistant application missing: $app" }
if (-not (Test-Path -LiteralPath $pythonRoot -PathType Container)) { throw "EZStudio_lab python root missing: $pythonRoot" }
$env:EZSTUDIOLAB_ASSISTANT_NODE_ID = $NodeId
$env:EZSTUDIO_SHARED_MODEL_ROOT = $SharedModelRoot
$env:EZSTUDIOLAB_ASSISTANT_MODEL_CACHE = $ModelCache
$env:EZSTUDIOLAB_HOST_REPO = $HostRepo
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$pythonRoot;$env:PYTHONPATH" } else { $pythonRoot }
if ($Mode -eq "capabilities") { & $Python $app capabilities; exit $LASTEXITCODE }
if ($Mode -eq "check-model") { if ([string]::IsNullOrWhiteSpace($Model)) { throw "-Model is required when -Mode check-model" }; & $Python $app check-job --model $Model; exit $LASTEXITCODE }
if ($Mode -in @("queue","watch","distributed-probe","distributed-watch")) {
    if ([string]::IsNullOrWhiteSpace($BaseUrl)) { throw "-BaseUrl is required" }
    if ([string]::IsNullOrWhiteSpace($Token)) { throw "-Token is required" }
    if ($Mode -eq "queue") { & $Python $app queue --base-url $BaseUrl --token $Token }
    elseif ($Mode -eq "watch") { & $Python $app watch --base-url $BaseUrl --token $Token --poll-seconds $PollSeconds --iterations $Iterations }
    elseif ($Mode -eq "distributed-probe") { & $Python $app distributed-probe --base-url $BaseUrl --token $Token --limit $Limit }
    else { & $Python $app distributed-watch --base-url $BaseUrl --token $Token --poll-seconds $PollSeconds --iterations $Iterations --limit $Limit }
    exit $LASTEXITCODE
}
if ($Mode -eq "evaluate-gate") { if ([string]::IsNullOrWhiteSpace($GateReport)) { throw "-GateReport is required" }; & $Python $app evaluate-gate $GateReport; exit $LASTEXITCODE }
throw "unsupported_mode:$Mode"
