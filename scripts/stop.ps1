$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installRoot = (Resolve-Path (Join-Path $root '..')).Path
$runtime = Join-Path $installRoot 'var\assistant\web'
$lockPath = Join-Path $runtime 'instance.lock'
$phpPidPath = Join-Path $runtime 'php.pid'
$caddyPidPath = Join-Path $runtime 'caddy.pid'

function Get-ProcessInfo([int]$ProcessId) {
    Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}

function Test-AssistantProcess([int]$ProcessId) {
    $p = Get-ProcessInfo $ProcessId
    if ($null -eq $p) { return $false }
    if ($p.Name -notin @('php.exe','caddy.exe')) { return $false }
    $cmd = [string]$p.CommandLine
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
    return $cmd.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Add-CandidatePid([System.Collections.Generic.HashSet[int]]$Set, $Value) {
    if ($null -eq $Value) { return }
    try { $pidValue = [int]$Value } catch { return }
    if (Test-AssistantProcess $pidValue) { [void]$Set.Add($pidValue) }
}

function Get-PortOwner([int]$Port) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) { return $null }
    return [int]$listener.OwningProcess
}

$candidates = [System.Collections.Generic.HashSet[int]]::new()

foreach ($pidPath in @($caddyPidPath, $phpPidPath)) {
    if (Test-Path -LiteralPath $pidPath -PathType Leaf) {
        try { Add-CandidatePid $candidates (Get-Content -LiteralPath $pidPath -Raw) } catch {}
    }
}

foreach ($port in @(8712,8713)) {
    $owner = Get-PortOwner $port
    Add-CandidatePid $candidates $owner
}

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @('php.exe','caddy.exe') -and
        -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
        ([string]$_.CommandLine).IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
    } |
    ForEach-Object { [void]$candidates.Add([int]$_.ProcessId) }

foreach ($targetPid in @($candidates)) {
    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($null -ne $proc) {
        Stop-Process -Id $targetPid -Force -ErrorAction Stop
        Wait-Process -Id $targetPid -ErrorAction SilentlyContinue
    }
}

Remove-Item -LiteralPath $caddyPidPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $phpPidPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction SilentlyContinue

Start-Sleep -Milliseconds 300

$left8712 = Get-PortOwner 8712
$left8713 = Get-PortOwner 8713
if ($null -ne $left8712 -or $null -ne $left8713) {
    throw "assistant_web_stop_incomplete: 8712_pid=$left8712 8713_pid=$left8713"
}

Write-Output "ASSISTANT_WEB_STOP_OK stopped=$($candidates.Count)"
