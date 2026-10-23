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
    # Engine readiness is independent of Web availability.
    $engine = Invoke-RestMethod -Uri 'http://127.0.0.1:8712/api/inference/status' -TimeoutSec 10 -ErrorAction Stop
    if ($engine.ok -ne $true -or $engine.state -ne 'READY' -or [string]::IsNullOrWhiteSpace([string]$engine.model)) {
        throw 'DEPLOY_INFERENCE_NOT_READY_OR_MODEL_UNIDENTIFIED'
    }
    $checks.inference = "engine=$($engine.engine);version=$($engine.engine_version);model=$($engine.model)"
    # Actual generation proof, never infer model availability from an HTTP /health alone.
    $probe = @{model=[string]$engine.model;messages=@(@{role='user';content='Reply with OK.'});max_tokens=8;temperature=0} | ConvertTo-Json -Depth 5 -Compress
    $generated = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8720/v1/chat/completions' -ContentType 'application/json' -Body $probe -TimeoutSec 45 -ErrorAction Stop
    $reply = [string]$generated.choices[0].message.content
    if ([string]::IsNullOrWhiteSpace($reply)) { throw 'DEPLOY_INFERENCE_EMPTY_GENERATION' }
    $checks.generation = 'response_nonempty'
    # Exercise the actual PROFILE advisory prompt against the loaded model,
    # with synthetic evidence only. Do not contact LAB or create a job.
    $assistantPython = Get-Command python.exe -ErrorAction Stop
    $profileSmoke = & $assistantPython.Source (Join-Path $root 'scripts\profile-live-smoke.py')
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_PROFILE_LIVE_SMOKE_FAILED' }
    $profileResult = $profileSmoke | ConvertFrom-Json -ErrorAction Stop
    if ($profileResult.ok -ne $true -or $profileResult.real_model -ne $true -or
        $profileResult.advisory_only -ne $true -or $profileResult.promotes_verdict -ne $false) {
        throw 'DEPLOY_PROFILE_LIVE_SMOKE_INVALID'
    }
    $checks.profile_live_smoke = $profileResult
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
        scope = 'assistant-web-and-inference; PROFILE job execution not certified'
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Output $state
    Write-Output "REPORT=$reportPath"
    if ($reason) { Write-Error -Message $reason -ErrorAction Continue }
}
if ($state -ne 'DEPLOYED_OK') { exit 1 }
