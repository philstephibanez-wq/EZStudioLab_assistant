param(
    [string]$Python = "python",
    [string]$NodeId = "EZStudioLab_assistant-$env:COMPUTERNAME",
    [Parameter(Mandatory=$true)][string]$SharedModelRoot,
    [string]$ModelCache = "$env:LOCALAPPDATA\EZStudioLab_assistant\models",
    [string]$HostRepo = "",
    [ValidateSet("capabilities","check-model")][string]$Mode = "capabilities",
    [string]$Model = ""
)

$ErrorActionPreference = "Stop"

$assistantRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$app = Join-Path $assistantRoot "app\main.py"

if ([string]::IsNullOrWhiteSpace($HostRepo)) {
    $HostRepo = Split-Path -Parent $assistantRoot
}
$pythonRoot = Join-Path $HostRepo "python"

if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {
    throw "EZStudioLab_assistant application missing: $app"
}
if (-not (Test-Path -LiteralPath $pythonRoot -PathType Container)) {
    throw "EZStudio_lab python root missing: $pythonRoot"
}

$env:EZSTUDIOLAB_ASSISTANT_NODE_ID = $NodeId
$env:EZSTUDIO_SHARED_MODEL_ROOT = $SharedModelRoot
$env:EZSTUDIOLAB_ASSISTANT_MODEL_CACHE = $ModelCache
$env:EZSTUDIOLAB_HOST_REPO = $HostRepo
$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$pythonRoot;$env:PYTHONPATH"
} else {
    $pythonRoot
}

if ($Mode -eq "capabilities") {
    & $Python $app capabilities
    exit $LASTEXITCODE
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    throw "-Model is required when -Mode check-model"
}

& $Python $app check-job --model $Model
exit $LASTEXITCODE
