$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installRoot = (Resolve-Path (Join-Path $root '..')).Path
$runtime = Join-Path $installRoot 'var\assistant\web'
$lockPath = Join-Path $runtime 'instance.lock'
$phpPidPath = Join-Path $runtime 'php.pid'
$caddyPidPath = Join-Path $runtime 'caddy.pid'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Get-LivePid([string]$pidPath) {
    if (-not (Test-Path -LiteralPath $pidPath -PathType Leaf)) { return $null }
    try { $targetPid = [int](Get-Content -LiteralPath $pidPath -Raw) }
    catch { Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue; return $null }
    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($null -eq $proc) { Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue; return $null }
    return $targetPid
}

function Get-AssistantPortsInUse {
    $p8712 = Get-NetTCPConnection -State Listen -LocalPort 8712 -ErrorAction SilentlyContinue
    $p8713 = Get-NetTCPConnection -State Listen -LocalPort 8713 -ErrorAction SilentlyContinue
    return [bool]($p8712 -or $p8713)
}

$phpPid = Get-LivePid $phpPidPath
$caddyPid = Get-LivePid $caddyPidPath
$portsInUse = Get-AssistantPortsInUse

if (Test-Path -LiteralPath $lockPath -PathType Container) {
    if ($null -ne $phpPid -and $null -ne $caddyPid) {
        Write-Output "ASSISTANT_WEB_ALREADY_RUNNING php_pid=$phpPid caddy_pid=$caddyPid http://EZSTUDIO-XPS:8712"
        exit 0
    }
    if ($null -ne $phpPid -or $null -ne $caddyPid -or $portsInUse) {
        throw "assistant_web_partial_instance_detected: php_pid=$phpPid caddy_pid=$caddyPid ports_in_use=$portsInUse; run scripts\stop.cmd before start"
    }
    Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction Stop
}

try {
    New-Item -ItemType Directory -Path $lockPath -ErrorAction Stop | Out-Null
} catch {
    Write-Output 'ASSISTANT_WEB_START_IN_PROGRESS_OR_RUNNING'
    exit 0
}

$phpProc = $null
$caddyProc = $null

try {
    $phpPid = Get-LivePid $phpPidPath
    $caddyPid = Get-LivePid $caddyPidPath
    $portsInUse = Get-AssistantPortsInUse
    if ($null -ne $phpPid -or $null -ne $caddyPid -or $portsInUse) {
        throw "assistant_web_instance_conflict_after_lock: php_pid=$phpPid caddy_pid=$caddyPid ports_in_use=$portsInUse"
    }

    $caddy = 'C:\Caddy\caddy.exe'
    if (-not (Test-Path -LiteralPath $caddy -PathType Leaf)) { $caddy = (Get-Command caddy.exe -ErrorAction Stop).Source }
    $php = $env:EZS_ASSISTANT_PHP
    if ([string]::IsNullOrWhiteSpace($php)) { $php = (Get-Command php.exe -ErrorAction Stop).Source }
    if (-not (Test-Path -LiteralPath (Join-Path $root 'vendor\autoload_runtime.php'))) { throw 'assistant_vendor_missing: run composer install in EZStudioLab_assistant' }

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

    Set-Content -LiteralPath (Join-Path $lockPath 'owner.txt') -Value @(
        "php_pid=$($phpProc.Id)",
        "caddy_pid=$($caddyProc.Id)",
        "root=$root",
        "started_at=$([DateTimeOffset]::Now.ToString('o'))"
    ) -Encoding utf8

    Write-Output "ASSISTANT_WEB_START_OK php_pid=$($phpProc.Id) caddy_pid=$($caddyProc.Id) http://EZSTUDIO-XPS:8712"
} catch {
    if ($null -ne $caddyProc -and -not $caddyProc.HasExited) { Stop-Process -Id $caddyProc.Id -Force -ErrorAction SilentlyContinue }
    if ($null -ne $phpProc -and -not $phpProc.HasExited) { Stop-Process -Id $phpProc.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $caddyPidPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $phpPidPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction SilentlyContinue
    throw
}
