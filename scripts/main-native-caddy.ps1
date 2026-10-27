# MAIN only: manual native Symfony + Caddy; no Orchestrator, Docker or LAB jobs.
[CmdletBinding()]
param([ValidateSet('Preflight','Start','Status','Stop')][string]$Action='Preflight')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$state = 'H:\temp\EZSTUDIO_ASSISTANT_NATIVE_MAIN'
$caddyPidFile = Join-Path $state 'caddy.pid'
$caddyConfig = Join-Path $state 'Caddyfile'
$webScript = Join-Path $PSScriptRoot 'main-native-web.ps1'
function Get-PortOwner([int]$port) {
    $p = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $p) { return $null }
    return [int]$p.OwningProcess
}
function Get-OurCaddy {
    if (-not (Test-Path $caddyPidFile -PathType Leaf)) { return $null }
    try { $targetPid = [int](Get-Content -LiteralPath $caddyPidFile -Raw) } catch { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$targetPid" -ErrorAction SilentlyContinue
    if ($null -eq $p -or $p.Name -ne 'caddy.exe') { return $null }
    $line=[string]$p.CommandLine
    if ($line.IndexOf($caddyConfig,[StringComparison]::OrdinalIgnoreCase) -lt 0) { return $null }
    return $p
}
function Resolve-Caddy {
    foreach ($path in @('H:\Caddy\caddy.exe','C:\Caddy\caddy.exe')) {
        if (Test-Path -LiteralPath $path -PathType Leaf) { return $path }
    }
    $cmd = Get-Command caddy.exe -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { throw 'MAIN_NATIVE_CADDY_MISSING' }
    return $cmd.Source
}
function Preflight {
    if (-not (Test-Path -LiteralPath $webScript)) { throw 'MAIN_NATIVE_WEB_SCRIPT_MISSING' }
    $caddy = Resolve-Caddy
    & $webScript -Action Preflight
    $owner = Get-PortOwner 18812
    $ours = Get-OurCaddy
    if ($null -ne $owner -and ($null -eq $ours -or $owner -ne [int]$ours.ProcessId)) {
        throw "MAIN_NATIVE_CADDY_FOREIGN_PORT_OWNER pid=$owner"
    }
    $versionLines = @(& $caddy version)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0 -or $versionLines.Count -eq 0) { throw 'MAIN_NATIVE_CADDY_INVALID' }
    Write-Output "MAIN_NATIVE_CADDY=$caddy version=$($versionLines[0])"
    Write-Output 'MAIN_NATIVE_CADDY_PREFLIGHT_OK'
}
function Probe([string]$url) {
    try {
        $response=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 12
        if ($response.StatusCode -ne 200) { return $false }
        return $true
    } catch { return $false }
}
switch($Action) {
 'Preflight' { Preflight }
 'Status' {
    & $webScript -Action Status
    $ours = Get-OurCaddy; $owner = Get-PortOwner 18812
    if ($null -ne $ours -and $owner -eq [int]$ours.ProcessId) {
        Write-Output "MAIN_NATIVE_CADDY_RUNNING pid=$owner url=http://127.0.0.1:18812/backoffice"
    } else { Write-Output "MAIN_NATIVE_CADDY_NOT_RUNNING owner=$owner" }
 }
 'Start' {
    Preflight
    & $webScript -Action Start
    $ours=Get-OurCaddy; $owner=Get-PortOwner 18812
    if ($null -ne $ours -and $owner -eq [int]$ours.ProcessId) {
        Write-Output "MAIN_NATIVE_CADDY_ALREADY_RUNNING pid=$owner"
    } else {
        New-Item -ItemType Directory -Force -Path $state | Out-Null
        # No global admin listener; all external access is disabled during pilot.
        $config = "{`n    admin off`n    auto_https off`n}`n127.0.0.1:18812 {`n    encode zstd gzip`n    reverse_proxy 127.0.0.1:18813`n}`n"
        [System.IO.File]::WriteAllText($caddyConfig,$config,[System.Text.UTF8Encoding]::new($false))
        $caddy=Resolve-Caddy
        $args=@('run','--config',('"'+$caddyConfig+'"'),'--adapter','caddyfile')
        $proc=Start-Process -FilePath $caddy -ArgumentList $args -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $state 'caddy.out.log') -RedirectStandardError (Join-Path $state 'caddy.err.log')
        Set-Content -LiteralPath $caddyPidFile -Value $proc.Id -Encoding ascii
        Start-Sleep -Milliseconds 900
        if ($proc.HasExited -or (Get-PortOwner 18812) -ne $proc.Id) { throw "MAIN_NATIVE_CADDY_START_FAILED: logs=$state" }
    }
    if (-not (Probe 'http://127.0.0.1:18812/backoffice')) {
        throw 'MAIN_NATIVE_CADDY_BACKOFFICE_HTTP_NOT_OK'
    }
    if (-not (Probe 'http://127.0.0.1:18812/assistant/gpu/telemetry')) {
        throw 'MAIN_NATIVE_CADDY_GPU_HTTP_NOT_OK'
    }
    Write-Output 'MAIN_NATIVE_STACK_OK http://127.0.0.1:18812/backoffice'
 }
 'Stop' {
    $ours=Get-OurCaddy; $owner=Get-PortOwner 18812
    if ($null -ne $ours -and $owner -eq [int]$ours.ProcessId) {
        Stop-Process -Id ([int]$ours.ProcessId) -ErrorAction Stop
        Remove-Item -LiteralPath $caddyPidFile -Force -ErrorAction SilentlyContinue
        Write-Output 'MAIN_NATIVE_CADDY_STOP_OK'
    } elseif ($null -ne $owner) {
        throw "MAIN_NATIVE_CADDY_STOP_REFUSED foreign_owner=$owner"
    }
    & $webScript -Action Stop
 }
}
