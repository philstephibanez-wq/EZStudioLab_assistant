$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installRoot = (Resolve-Path (Join-Path $root '..')).Path
$runtime = Join-Path $installRoot 'var\assistant\web'
$lockPath = Join-Path $runtime 'instance.lock'

foreach ($name in @('caddy','php')) {
    $pidPath = Join-Path $runtime ($name + '.pid')
    if (-not (Test-Path -LiteralPath $pidPath -PathType Leaf)) { continue }

    try {
        $targetPid = [int](Get-Content -LiteralPath $pidPath -Raw)
    } catch {
        Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
        continue
    }

    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($null -ne $proc) {
        Stop-Process -Id $targetPid -Force -ErrorAction Stop
        Wait-Process -Id $targetPid -ErrorAction SilentlyContinue
    }

    Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $lockPath -Recurse -Force -ErrorAction SilentlyContinue
Write-Output 'ASSISTANT_WEB_STOP_OK'
