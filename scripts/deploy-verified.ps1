#Requires -Version 5.1
# EZStudioLab Assistant: fail-closed deployment of the Web entrypoint only.
# Does not install/start legacy PROFILE workers, restart Qwen or alter LAB data.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$reportDir = Join-Path $root 'runtime\deploy'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$reportPath = Join-Path $reportDir 'latest.json'
$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$checks = [ordered]@{}
$state = 'DEPLOY_FAILED'
$reason = ''
$version = ''
$sha = ''
$before = ''
try {
    $branch = (& git -C $root branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw "DEPLOY_BRANCH_NOT_MAIN:$branch" }
    $checks.branch = 'main'
    $dirty = @(& git -C $root status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'DEPLOY_TRACKED_TREE_DIRTY' }
    $checks.git_clean = $true
    & git -C $root fetch --quiet origin main
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_FETCH_FAILED' }
    $before = (& git -C $root rev-parse HEAD).Trim()
    $remote = (& git -C $root rev-parse origin/main).Trim()
    $base = (& git -C $root merge-base HEAD origin/main).Trim()
    if ($LASTEXITCODE -ne 0 -or $base -ne $before) { throw 'DEPLOY_NOT_FAST_FORWARD' }

    # Check installed dependencies before touching a running service.
    foreach ($file in @('vendor\autoload_runtime.php','public\index.php','scripts\stop-web.ps1','scripts\start-web.ps1')) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $file) -PathType Leaf)) {
            throw "DEPLOY_DEPENDENCY_MISSING:$file"
        }
    }
    $checks.dependencies = 'present'
    & git -C $root merge --ff-only origin/main
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_MERGE_FAILED' }
    $sha = (& git -C $root rev-parse HEAD).Trim()
    $version = (Get-Content (Join-Path $root 'VERSION') -Raw).Trim()
    if ($version -notmatch '^\d+\.\d+[a-z]\(\d+\)$') { throw 'DEPLOY_VERSION_INVALID' }
    $checks.code = "sha=$sha;version=$version"
    $php = Get-Command php.exe -ErrorAction Stop
    & $php.Source -l (Join-Path $root 'src\Controller\DashboardController.php') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_PHP_LINT_FAILED' }
    $checks.php_lint = 'ok'

    & (Join-Path $PSScriptRoot 'stop-web.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_WEB_STOP_FAILED' }
    $checks.stop = 'ok'
    & (Join-Path $PSScriptRoot 'start-web.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_WEB_START_FAILED' }
    $checks.start = 'ok'
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8712/api/health' -TimeoutSec 10 -ErrorAction Stop
    if ($health.ok -ne $true -or $health.version -ne $version -or $health.persistence_owner -ne 'LAB') {
        throw "DEPLOY_HEALTH_MISMATCH:expected=$version;actual=$($health.version)"
    }
    $checks.health = "version=$($health.version);persistence=LAB"
    $listeners = @(8712,8713 | ForEach-Object {
        Get-NetTCPConnection -State Listen -LocalPort $_ -ErrorAction Stop | Select-Object -First 1
    })
    if ($listeners.Count -ne 2) { throw 'DEPLOY_LISTENERS_MISSING' }
    $checks.listeners = @($listeners | ForEach-Object { [string]$_.OwningProcess })
    $state = 'DEPLOYED_OK'
} catch {
    $reason = $_.Exception.Message
} finally {
    $report = [ordered]@{
        schema = 'ezstudio.assistant.web-deployment.v1'
        state = $state
        started_at = $startedAt
        finished_at = [DateTimeOffset]::UtcNow.ToString('o')
        root = $root
        before_sha = $before
        deployed_sha = $sha
        version = $version
        checks = $checks
        failure = $reason
        scope = 'assistant-web-only; PROFILE job execution not certified'
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Output $state
    Write-Output "REPORT=$reportPath"
    if ($reason) { Write-Error -Message $reason -ErrorAction Continue }
}
if ($state -ne 'DEPLOYED_OK') { exit 1 }
