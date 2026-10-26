$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = Join-Path $root 'runtime\web'
$lockPath = Join-Path $runtime 'instance.lock'
$phpPidPath = Join-Path $runtime 'php.pid'
$caddyPidPath = Join-Path $runtime 'caddy.pid'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

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

function Get-LiveAssistantPid([string]$PidPath) {
    if (-not (Test-Path -LiteralPath $PidPath -PathType Leaf)) { return $null }
    try { $candidate = [int](Get-Content -LiteralPath $PidPath -Raw) }
    catch {
        Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
        return $null
    }
    if (Test-AssistantProcess $candidate) { return $candidate }
    Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
    return $null
}

function Get-PortOwner([int]$Port) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) { return $null }
    return [int]$listener.OwningProcess
}

function New-SingletonLock {
    try {
        New-Item -ItemType Directory -Path $lockPath -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

$phpPid = Get-LiveAssistantPid $phpPidPath
$caddyPid = Get-LiveAssistantPid $caddyPidPath
$owner8712 = Get-PortOwner 8712
$owner8713 = Get-PortOwner 8713

$assistantOn8712 = $null -ne $owner8712 -and (Test-AssistantProcess $owner8712)
$assistantOn8713 = $null -ne $owner8713 -and (Test-AssistantProcess $owner8713)

if ($assistantOn8712 -and $assistantOn8713) {
    $caddyPid = $owner8712
    $phpPid = $owner8713
    Set-Content -LiteralPath $caddyPidPath -Value $caddyPid -Encoding ascii
    Set-Content -LiteralPath $phpPidPath -Value $phpPid -Encoding ascii
    if (-not (Test-Path -LiteralPath $lockPath -PathType Container)) {
        New-Item -ItemType Directory -Path $lockPath -Force | Out-Null
    }
    Set-Content -LiteralPath (Join-Path $lockPath 'owner.txt') -Value @(
        "php_pid=$phpPid",
        "caddy_pid=$caddyPid",
        "root=$root",
        "recovered_at=$([DateTimeOffset]::Now.ToString('o'))"
    ) -Encoding utf8
    Write-Output "ASSISTANT_WEB_ALREADY_RUNNING php_pid=$phpPid caddy_pid=$caddyPid http://EZSTUDIO-XPS:8712"
    exit 0
}

if (($null -ne $owner8712 -and -not $assistantOn8712) -or ($null -ne $owner8713 -and -not $assistantOn8713)) {
    throw "assistant_web_foreign_port_owner: 8712_pid=$owner8712 8713_pid=$owner8713"
}

if ($assistantOn8712 -or $assistantOn8713 -or $null -ne $phpPid -or $null -ne $caddyPid) {
    throw "assistant_web_partial_instance_detected: php_pid=$phpPid caddy_pid=$caddyPid 8712_pid=$owner8712 8713_pid=$owner8713; run scripts\stop.cmd before start"
}

if (Test-Path -LiteralPath $lockPath -PathType Container) {
    Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction Stop
}
if (-not (New-SingletonLock)) {
    Write-Output 'ASSISTANT_WEB_START_IN_PROGRESS_OR_RUNNING'
    exit 0
}

$phpProc = $null
$caddyProc = $null

try {
    $caddy = 'H:\Caddy\caddy.exe'
    if (-not (Test-Path -LiteralPath $caddy -PathType Leaf)) { $caddy = 'C:\Caddy\caddy.exe' }
    if (-not (Test-Path -LiteralPath $caddy -PathType Leaf)) {
        $caddy = (Get-Command caddy.exe -ErrorAction Stop).Source
    }

    $php = $env:EZS_ASSISTANT_PHP
    if ([string]::IsNullOrWhiteSpace($php)) {
        $php = (Get-Command php.exe -ErrorAction Stop).Source
    }

    if (-not (Test-Path -LiteralPath (Join-Path $root 'vendor\autoload_runtime.php'))) {
        throw 'assistant_vendor_missing: run composer install in EZStudioLab_assistant'
    }

    $phpOut = Join-Path $runtime 'php.out.log'
    $phpErr = Join-Path $runtime 'php.err.log'
    $caddyOut = Join-Path $runtime 'caddy.out.log'
    $caddyErr = Join-Path $runtime 'caddy.err.log'

    $phpArgs = @('-S','127.0.0.1:8713','-t',(Join-Path $root 'public'),(Join-Path $root 'public\index.php'))
    $phpProc = Start-Process -FilePath $php -ArgumentList $phpArgs -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $phpOut -RedirectStandardError $phpErr -PassThru
    Set-Content -LiteralPath $phpPidPath -Value $phpProc.Id -Encoding ascii

    Start-Sleep -Milliseconds 800
    if ($phpProc.HasExited) { throw "assistant_php_start_failed: exit=$($phpProc.ExitCode)" }

    $caddyArgs = @('run','--config',(Join-Path $root 'Caddyfile'),'--adapter','caddyfile')
    $caddyProc = Start-Process -FilePath $caddy -ArgumentList $caddyArgs -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $caddyOut -RedirectStandardError $caddyErr -PassThru
    Set-Content -LiteralPath $caddyPidPath -Value $caddyProc.Id -Encoding ascii

    Start-Sleep -Milliseconds 500
    if ($caddyProc.HasExited) { throw "assistant_caddy_start_failed: exit=$($caddyProc.ExitCode)" }

    $owner8712 = Get-PortOwner 8712
    $owner8713 = Get-PortOwner 8713
    if ($owner8712 -ne $caddyProc.Id -or $owner8713 -ne $phpProc.Id) {
        throw "assistant_web_listener_validation_failed: expected_caddy=$($caddyProc.Id) actual_8712=$owner8712 expected_php=$($phpProc.Id) actual_8713=$owner8713"
    }

    Set-Content -LiteralPath (Join-Path $lockPath 'owner.txt') -Value @(
        "php_pid=$($phpProc.Id)",
        "caddy_pid=$($caddyProc.Id)",
        "root=$root",
        "started_at=$([DateTimeOffset]::Now.ToString('o'))"
    ) -Encoding utf8

    Write-Output "ASSISTANT_WEB_START_OK php_pid=$($phpProc.Id) caddy_pid=$($caddyProc.Id) http://EZSTUDIO-XPS:8712"
} catch {
    if ($null -ne $caddyProc -and -not $caddyProc.HasExited) {
        Stop-Process -Id $caddyProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $phpProc -and -not $phpProc.HasExited) {
        Stop-Process -Id $phpProc.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $caddyPidPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $phpPidPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction SilentlyContinue
    throw
}
