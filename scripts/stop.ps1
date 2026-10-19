$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$webStop = Join-Path $PSScriptRoot 'stop-web.ps1'
$live = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -in @('python.exe','pythonw.exe') -and
    $_.CommandLine -match 'profile_ai_requests_worker\.py' -and
    $_.CommandLine -match '(?i)EZStudioLab_assistant'
})
if ($live.Count -gt 0) {
    throw 'ASSISTANT_SAFE_STOP_REFUSED: PROFILE worker is active; no atomic LAB/Orchestrator idle proof. No services stopped. Do not kill an active scientific job.'
}
# Do not terminate Qwen unless the service is owned by this instance and PROFILE is absent.
$conn = Get-NetTCPConnection -State Listen -LocalPort 8720 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -ne $conn) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($conn.OwningProcess)" -ErrorAction SilentlyContinue
    if ($null -eq $p -or $p.Name -ne 'llama-server.exe' -or
        $p.CommandLine -notmatch [regex]::Escape($root) -or
        $p.CommandLine -notmatch 'qwen2\.5-1\.5b-instruct-q4_k_m') {
        throw 'ASSISTANT_SAFE_STOP_REFUSED: Qwen port is not demonstrably owned by this assistant. No services stopped.'
    }
}
if (-not (Test-Path -LiteralPath $webStop -PathType Leaf)) { throw 'ASSISTANT_STOP_WEB_MISSING' }
# Stop only after all preflights pass; the existing web script targets this repository only.
& $webStop
if ($LASTEXITCODE -ne 0) { throw "ASSISTANT_WEB_STOP_FAILED exit=$LASTEXITCODE" }
if ($null -ne $conn) {
    $check = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ProcessId)" -ErrorAction SilentlyContinue
    if ($null -ne $check -and $check.CreationDate -eq $p.CreationDate) {
        Stop-Process -Id $p.ProcessId -ErrorAction Stop
    }
}
Write-Output 'ASSISTANT_STACK_STOP_OK (PROFILE already absent)'
