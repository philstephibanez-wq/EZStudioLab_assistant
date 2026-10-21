# Diagnostic non destructif PROFILE XPS (aucun jeton affiché, aucun processus arrêté)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$launcher = Join-Path $root 'runtime\start_profile_ai_requests.ps1'
$var = 'EZSTUDIOLAB_REVIEW_PRESET_PATH'
$path = [Environment]::GetEnvironmentVariable($var, 'Process')
if (-not $path) { $path = [Environment]::GetEnvironmentVariable($var, 'User') }
if (-not $path) { $path = [Environment]::GetEnvironmentVariable($var, 'Machine') }
Write-Output ('PRESET_ENV_CONFIGURED=' + [bool]$path)
if ($path) {
    $unc = $path.StartsWith('\\')
    Write-Output ('PRESET_ENV_UNC=' + $unc)
    Write-Output ('PRESET_FILE_ACCESSIBLE=' + (Test-Path -LiteralPath $path -PathType Leaf))
}
Write-Output ('PROFILE_LOCAL_LAUNCHER_PRESENT=' + (Test-Path -LiteralPath $launcher -PathType Leaf))
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
    $source = Get-Content -LiteralPath $launcher -Raw
    Write-Output ('LAUNCHER_MENTIONS_PRESET_PATH=' + $source.Contains($var))
    Write-Output ('LAUNCHER_MENTIONS_PRESET_FILE=' + $source.Contains('profile-baseline-1.json'))
}
$guardian = Join-Path $root 'app\profile_guardian.py'
$worker = Join-Path $root 'runtime\profile_ai_requests_worker.py'
$processes = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and
    ($_.CommandLine.Contains($guardian) -or $_.CommandLine.Contains($worker))
})
Write-Output ('PROFILE_PROCESS_COUNT=' + $processes.Count)
Write-Output ('PROFILE_GUARDIAN_COUNT=' + @($processes | Where-Object { $_.CommandLine.Contains($guardian) }).Count)
Write-Output ('PROFILE_WORKER_COUNT=' + @($processes | Where-Object { $_.CommandLine.Contains($worker) }).Count)
Write-Output 'PROFILE_DIAGNOSTIC_READONLY_OK'
