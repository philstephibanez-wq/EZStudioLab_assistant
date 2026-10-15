$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installRoot = (Resolve-Path (Join-Path $root '..')).Path
$runtime = Join-Path $installRoot 'var\assistant\web'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$caddy = 'C:\Caddy\caddy.exe'
if (-not (Test-Path -LiteralPath $caddy -PathType Leaf)) { $caddy = (Get-Command caddy.exe -ErrorAction Stop).Source }
$php = $env:EZS_ASSISTANT_PHP
if ([string]::IsNullOrWhiteSpace($php)) { $php = (Get-Command php.exe -ErrorAction Stop).Source }
if (-not (Test-Path -LiteralPath (Join-Path $root 'vendor\autoload_runtime.php'))) { throw 'assistant_vendor_missing: run composer install in EZStudioLab_assistant' }
$phpOut=Join-Path $runtime 'php.out.log'; $phpErr=Join-Path $runtime 'php.err.log'; $caddyOut=Join-Path $runtime 'caddy.out.log'; $caddyErr=Join-Path $runtime 'caddy.err.log'
$phpProc=Start-Process -FilePath $php -ArgumentList @('-S','127.0.0.1:8713','-t',(Join-Path $root 'public'),(Join-Path $root 'public\index.php')) -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $phpOut -RedirectStandardError $phpErr -PassThru
Set-Content -LiteralPath (Join-Path $runtime 'php.pid') -Value $phpProc.Id -Encoding ascii
Start-Sleep -Milliseconds 800
$caddyProc=Start-Process -FilePath $caddy -ArgumentList @('run','--config',(Join-Path $root 'Caddyfile'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $caddyOut -RedirectStandardError $caddyErr -PassThru
Set-Content -LiteralPath (Join-Path $runtime 'caddy.pid') -Value $caddyProc.Id -Encoding ascii
Write-Output 'ASSISTANT_WEB_START_OK http://EZSTUDIO-XPS:8712'
