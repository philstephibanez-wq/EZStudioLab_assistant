$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$webStart = Join-Path $PSScriptRoot 'start-web.ps1'
$guardian = Join-Path $root 'app\profile_guardian.py'
$profileWorker = Join-Path $root 'runtime\profile_ai_requests_worker.py'
$qwenExe = Join-Path $root 'runtime\ai\bin\llama-server.exe'
$qwenModel = Join-Path $root 'runtime\models-cache\assistant\bench\qwen2.5-1.5b-instruct-q4_k_m\qwen2.5-1.5b-instruct-q4_k_m.gguf'
$logDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Get-Listener([int]$Port) {
  $conn=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $conn) { return $null }
  Get-CimInstance Win32_Process -Filter "ProcessId=$($conn.OwningProcess)" -ErrorAction Stop
}
function Get-Workers {
  @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and
    $_.CommandLine.IndexOf($profileWorker,[StringComparison]::OrdinalIgnoreCase) -ge 0
  })
}
function Get-Guardians {
  @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and
    $_.CommandLine.IndexOf($guardian,[StringComparison]::OrdinalIgnoreCase) -ge 0
  })
}
function Wait-For([scriptblock]$test,[int]$seconds,[string]$failure) {
  $end=[DateTime]::UtcNow.AddSeconds($seconds)
  do {
    if (& $test) { return }
    Start-Sleep -Milliseconds 500
  } while ([DateTime]::UtcNow -lt $end)
  throw $failure
}
function Qwen-Ready {
  try {
    $v=Invoke-RestMethod 'http://127.0.0.1:8720/health' -TimeoutSec 3 -ErrorAction Stop
    return $v.status -in @('ok','ready')
  } catch { return $false }
}
function Assert-Qwen-Context([string]$path) {
  # Prove exact launch parameters; health alone does not verify context capacity.
  $proc=Get-Listener 8720
  if ($null -eq $proc -or $proc.Name -ne 'llama-server.exe' -or
      -not $proc.CommandLine -or $proc.CommandLine.IndexOf($qwenModel,[StringComparison]::OrdinalIgnoreCase) -lt 0) {
    throw 'QWEN_PORT_OWNER_NOT_EXPECTED'
  }
  $cmd=[string]$proc.CommandLine
  if ($cmd -notmatch '(?i)(?:^|\s)(?:-c|--ctx-size)\s+8192(?:\s|$)' -or
      $cmd -notmatch '(?i)(?:^|\s)(?:-np|--parallel)\s+1(?:\s|$)') {
    throw 'QWEN_CONTEXT_CONFIG_INCOMPATIBLE: expected -c 8192 -np 1; existing instance not killed. Stop only when inference is idle, then rerun start.'
  }
  if (-not (Qwen-Ready)) { throw 'QWEN_NOT_READY' }
  Write-Output "QWEN_READY pid=$($proc.ProcessId) context=8192 slots=1"
}

# Validate dependencies before changing any service.
foreach ($p in @($webStart,$qwenExe,$qwenModel,$guardian,(Join-Path $root 'runtime\start_profile_ai_requests.ps1'))) {
  if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "ASSISTANT_REQUIRED_FILE_MISSING:$p" }
}
if (@(Get-Workers).Count -gt 1) { throw 'PROFILE_DUPLICATE_WORKERS' }
if (@(Get-Guardians).Count -gt 1) { throw 'PROFILE_DUPLICATE_GUARDIANS' }

& $webStart
if ($LASTEXITCODE -ne 0) { throw 'ASSISTANT_WEB_START_FAILED' }
Wait-For { $null -ne (Get-Listener 8712) -and $null -ne (Get-Listener 8713) } 10 'ASSISTANT_WEB_NOT_LISTENING'
Write-Output 'ASSISTANT_WEB_READY'

$owner=Get-Listener 8720
if ($null -eq $owner) {
  $args=@('-m',('"'+$qwenModel+'"'),'--host','127.0.0.1','--port','8720','-c','8192','-np','1')
  $q=Start-Process -FilePath $qwenExe -ArgumentList $args -WorkingDirectory $root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logDir 'qwen.out.log') `
    -RedirectStandardError (Join-Path $logDir 'qwen.err.log')
  Wait-For {
    if ($q.HasExited) { throw "QWEN_EXITED:$($q.ExitCode)" }
    Qwen-Ready
  } 120 'QWEN_START_TIMEOUT'
}
Assert-Qwen-Context $qwenModel

# Existing worker is left untouched; guardian waits for it instead of duplicating.
$guardians=@(Get-Guardians)
if ($guardians.Count -eq 0) {
  $python='C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
  if (-not (Test-Path $python -PathType Leaf)) { throw 'PROFILE_PYTHON_ABSENT' }
  $p=Start-Process -FilePath $python -ArgumentList @('-u',('"'+$guardian+'"')) -WorkingDirectory $root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logDir 'profile-guardian.out.log') `
    -RedirectStandardError (Join-Path $logDir 'profile-guardian.err.log')
  Wait-For { @(Get-Guardians).Count -eq 1 } 10 'PROFILE_GUARDIAN_NOT_STARTED'
  Write-Output "PROFILE_GUARDIAN_READY pid=$($p.Id)"
} else { Write-Output "PROFILE_GUARDIAN_ALREADY_RUNNING pid=$($guardians[0].ProcessId)" }
Wait-For { @(Get-Workers).Count -eq 1 } 40 'PROFILE_WORKER_NOT_RUNNING: see logs\profile-ai-requests.log and logs\profile-guardian.err.log'
Start-Sleep -Seconds 2
if (@(Get-Workers).Count -ne 1 -or @(Get-Guardians).Count -ne 1) { throw 'PROFILE_NOT_PERSISTENT' }
Write-Output "PROFILE_READY pid=$(@(Get-Workers)[0].ProcessId)"
Write-Output 'ASSISTANT_STACK_START_OK (web+qwen+guardian+profile; scientific result not verified)'
