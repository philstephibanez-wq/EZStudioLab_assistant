$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installRoot = (Resolve-Path (Join-Path $root '..')).Path
$runtime = Join-Path $installRoot 'var\assistant\web'
foreach ($name in @('caddy','php')) {
  $pidPath=Join-Path $runtime ($name+'.pid'); if (-not (Test-Path -LiteralPath $pidPath -PathType Leaf)) { continue }
  $targetPid=[int](Get-Content -LiteralPath $pidPath -Raw); $proc=Get-Process -Id $targetPid -ErrorAction SilentlyContinue
  if ($null -ne $proc) { Stop-Process -Id $targetPid -ErrorAction Stop; Wait-Process -Id $targetPid -ErrorAction SilentlyContinue }
  Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
}
Write-Output 'ASSISTANT_WEB_STOP_OK'
