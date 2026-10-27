# MAIN native Symfony pilot; intentionally isolated from existing Docker/XPS.
# Windows PowerShell 5.1 compatible. No Docker lifecycle operations.
[CmdletBinding()]
param([ValidateSet('Preflight','Start','Status','Stop')][string]$Action='Preflight')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$state = 'H:\temp\EZSTUDIO_ASSISTANT_NATIVE_MAIN'
$pidFile = Join-Path $state 'web.pid'
$port = 18813
function Get-Owner {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) { return $null }
    return [int]$listener.OwningProcess
}
function Get-OurProcess {
    if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
    try { $id = [int](Get-Content -LiteralPath $pidFile -Raw) } catch { return $null }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    if ($null -eq $proc -or $proc.Name -ne 'php.exe') { return $null }
    $line = [string]$proc.CommandLine
    if ($line.IndexOf('127.0.0.1:18813',[StringComparison]::OrdinalIgnoreCase) -lt 0) { return $null }
    if ($line.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -lt 0) { return $null }
    return $proc
}
function Resolve-Php {
    $binary = $env:EZS_ASSISTANT_PHP
    if ([string]::IsNullOrWhiteSpace($binary)) {
        $cmd = Get-Command php.exe -ErrorAction SilentlyContinue
        if ($null -eq $cmd) { throw 'MAIN_NATIVE_PHP_MISSING: configure EZS_ASSISTANT_PHP' }
        $binary = $cmd.Source
    }
    if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw 'MAIN_NATIVE_PHP_PATH_MISSING' }
    return $binary
}
function Preflight {
    $binary = Resolve-Php
    if (-not (Test-Path (Join-Path $root 'vendor\autoload_runtime.php'))) {
        throw 'MAIN_NATIVE_VENDOR_MISSING: composer install is required (do not modify Docker)'
    }
    if (-not (Test-Path (Join-Path $root 'public\index.php'))) { throw 'MAIN_NATIVE_FRONT_CONTROLLER_MISSING' }
    $owner = Get-Owner
    $ours = Get-OurProcess
    if ($null -ne $owner -and ($null -eq $ours -or $owner -ne [int]$ours.ProcessId)) {
        throw "MAIN_NATIVE_PORT_IN_USE_18813: pid=$owner"
    }
    $phpVersionLines = @(& $binary -v)
    $phpExitCode = $LASTEXITCODE
    if ($phpExitCode -ne 0 -or $phpVersionLines.Count -eq 0) { throw 'MAIN_NATIVE_PHP_INVALID' }
    Write-Output ([string]$phpVersionLines[0])
    $gpu = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($null -eq $gpu) { Write-Output 'MAIN_NATIVE_GPU_PROBE_NOT_FOUND' }
    else { Write-Output "MAIN_NATIVE_GPU_PROBE=$($gpu.Source)" }
    Write-Output "MAIN_NATIVE_PREFLIGHT_OK port=$port version=$((Get-Content (Join-Path $root 'VERSION') -Raw).Trim())"
}
switch ($Action) {
 'Preflight' { Preflight }
 'Status' {
    $proc = Get-OurProcess
    $owner = Get-Owner
    if ($null -eq $proc -or $owner -ne [int]$proc.ProcessId) {
        Write-Output "MAIN_NATIVE_NOT_RUNNING owner=$owner"
    } else { Write-Output "MAIN_NATIVE_RUNNING pid=$($proc.ProcessId) url=http://127.0.0.1:$port/backoffice" }
 }
 'Start' {
    Preflight
    $ours = Get-OurProcess
    if ($null -ne $ours) { Write-Output "MAIN_NATIVE_ALREADY_RUNNING pid=$($ours.ProcessId)"; break }
    New-Item -ItemType Directory -Force -Path $state | Out-Null
    $binary = Resolve-Php
    $args = @('-S','127.0.0.1:18813','-t',(Join-Path $root 'public'),(Join-Path $root 'public\index.php'))
    $process = Start-Process -FilePath $binary -ArgumentList $args -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $state 'web.out.log') -RedirectStandardError (Join-Path $state 'web.err.log')
    Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ascii
    Start-Sleep -Milliseconds 900
    if ($process.HasExited -or (Get-Owner) -ne $process.Id) {
        Write-Output "MAIN_NATIVE_START_FAILED logs=$state"
        throw 'MAIN_NATIVE_PROCESS_NOT_LISTENING'
    }
    Write-Output "MAIN_NATIVE_STARTED pid=$($process.Id) url=http://127.0.0.1:$port/backoffice"
 }
 'Stop' {
    $ours = Get-OurProcess
    if ($null -eq $ours -or (Get-Owner) -ne [int]$ours.ProcessId) {
        throw 'MAIN_NATIVE_STOP_REFUSED: process not positively identified'
    }
    Stop-Process -Id ([int]$ours.ProcessId) -ErrorAction Stop
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Output 'MAIN_NATIVE_STOP_OK'
 }
}
