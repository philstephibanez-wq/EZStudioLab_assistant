# Guardian-managed PROFILE-only reload using LAB canonical queue maintenance.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$workerFile=Join-Path $root 'runtime\profile_ai_requests_worker.py'
$guardianFile=Join-Path $root 'app\profile_guardian.py'
# Discover existing credentials without executing the local launcher or printing them.
function Get-ProfileConfig([string]$name) {
 foreach($scope in @('Process','User','Machine')) {
  $value=[Environment]::GetEnvironmentVariable($name,$scope)
  if($value){return [string]$value}
 }
 $launcher=Join-Path $root 'runtime\start_profile_ai_requests.ps1'
 if(-not (Test-Path -LiteralPath $launcher -PathType Leaf)){return ''}
 $tokens=$null;$errors=$null
 $ast=[System.Management.Automation.Language.Parser]::ParseFile($launcher,[ref]$tokens,[ref]$errors)
 if(@($errors).Count -gt 0){throw 'PROFILE_LAUNCHER_PARSE_ERROR'}
 $matches=@($ast.FindAll({
  param($node)
  $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
  $node.Left.Extent.Text -ieq ('$env:'+$name)
 },$true))
 if($matches.Count -ne 1){return ''}
 $rhs=$matches[0].Right
 if($rhs -is [System.Management.Automation.Language.CommandExpressionAst]){$rhs=$rhs.Expression}
 if($rhs -is [System.Management.Automation.Language.StringConstantExpressionAst]){return [string]$rhs.Value}
 # Explicitly accept PSCredential.GetNetworkCredential().Password, not arbitrary expressions.
 if($name -eq 'EZSTUDIOLAB_ASSISTANT_TOKEN' -and
    $rhs -is [System.Management.Automation.Language.MemberExpressionAst] -and
    $rhs.Member.Extent.Text -eq 'Password' -and
    $rhs.Expression -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and
    $rhs.Expression.Member.Extent.Text -eq 'GetNetworkCredential' -and
    $rhs.Expression.Expression -is [System.Management.Automation.Language.VariableExpressionAst]) {
   $credVar=$rhs.Expression.Expression.VariablePath.UserPath
   $sources=@($ast.FindAll({
      param($node)
      $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
      $node.Left.Extent.Text -ieq ('
}
$relay=Get-ProfileConfig 'EZSTUDIOLAB_ASSISTANT_BASE_URL'
if(-not $relay){$relay='http://EZSTUDIO-MAIN:8702'}
$token=Get-ProfileConfig 'EZSTUDIOLAB_ASSISTANT_TOKEN'
if (-not $relay -or -not $token) { throw 'PROFILE_RELOAD_LAB_TOKEN_UNAVAILABLE_IN_APPROVED_SOURCES' }
$uri=$null
if (-not [Uri]::TryCreate($relay,[UriKind]::Absolute,[ref]$uri) -or
 $uri.Scheme -notin @('http','https') -or -not $uri.Host -or $uri.UserInfo) {
 throw 'PROFILE_RELAY_URL_INVALID'
}

function Maintenance([string]$mode) {
 $suffix='/internal/analysis/desktop/profile/ai-requests/maintenance'
 
 $method=if($mode -eq 'status'){'GET'}else{'POST'}
 $args=@{Method=$method;Uri=($relay.TrimEnd('/')+$suffix);Headers=@{'X-EZScore-Analysis-Token'=$token};TimeoutSec=8}
 if($method -eq 'POST'){$args.ContentType='application/json';$args.Body=('{"mode":"'+$mode+'"}')}
 $v=Invoke-RestMethod @args
 if($v.ok -ne $true){throw "PROFILE_LAB_MAINTENANCE_FAILED:$mode"}
 return $v
}
function Processes([string]$path) {
 @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
  $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and
  $_.CommandLine.IndexOf($path,[StringComparison]::OrdinalIgnoreCase) -ge 0
 })
}
$paused=$false
$reloadSucceeded=$false
try {
 $v=Maintenance 'pause';$paused=$true
 if($v.maintenance -ne $true -or $v.active -ne $false){throw 'PROFILE_MAINTENANCE_NOT_IDLE'}
 $jobs=Invoke-RestMethod 'http://EZSTUDIO-MAIN:8700/api/jobs' -TimeoutSec 8
 if($jobs.ok -ne $true -or $null -eq $jobs.jobs -or $null -eq $jobs.queue_errors){throw 'ORCHESTRATOR_QUEUE_STATUS_UNVERIFIED'}
 if($jobs.queue_errors.PSObject.Properties.Name -contains 'lab_ai'){throw 'ORCHESTRATOR_PROFILE_QUEUE_UNREADABLE'}
 if(@($jobs.jobs | Where-Object {$_.kind -eq 'assistant.profile.review' -and $_.state -in @('running','claimed','cancelling')}).Count -gt 0){throw 'PROFILE_ACTIVE_JOB'}
 $g=@(Processes $guardianFile);$w=@(Processes $workerFile)
 if($g.Count -ne 1 -or $w.Count -ne 1){throw "PROFILE_PROCESS_COUNTS_INVALID guardian=$($g.Count) worker=$($w.Count)"}
 $old=$w[0]
 $check=Maintenance 'status'
 if($check.maintenance -ne $true -or $check.active -ne $false){throw 'PROFILE_RELOAD_LOST_MAINTENANCE'}
 $now=Get-CimInstance Win32_Process -Filter "ProcessId=$($old.ProcessId)"
 if($null -eq $now -or $now.CreationDate -ne $old.CreationDate -or $now.CommandLine.IndexOf($workerFile,[StringComparison]::OrdinalIgnoreCase) -lt 0){throw 'PROFILE_WORKER_PID_RACE'}
 Stop-Process -Id $old.ProcessId -ErrorAction Stop
 $until=(Get-Date).AddSeconds(45)
 do {
  Start-Sleep -Seconds 2
  $g=@(Processes $guardianFile);$w=@(Processes $workerFile)
  if($g.Count -ne 1 -or $w.Count -gt 1){throw 'PROFILE_GUARDIAN_OR_WORKER_DUPLICATED'}
  if($w.Count -eq 1 -and $w[0].ProcessId -ne $old.ProcessId){break}
 }while((Get-Date) -lt $until)
 if($w.Count -ne 1 -or $w[0].ProcessId -eq $old.ProcessId){throw 'PROFILE_GUARDIAN_RELOAD_TIMEOUT'}
 $reloadSucceeded=$true
 Write-Output "PROFILE_WORKER_RELOADED old=$($old.ProcessId) new=$($w[0].ProcessId)"
}finally{
 if($paused){
  $status=Maintenance 'status'
  if($reloadSucceeded -and $status.maintenance -eq $true -and $status.active -eq $false){
   [void](Maintenance 'resume')
   Write-Output 'PROFILE_QUEUE_RESUMED'
  }else{Write-Warning 'PROFILE_QUEUE_REMAINS_PAUSED_FOR_SAFETY'}
 }
}
+$credVar)
   },$true))
   if($sources.Count -ne 1){throw 'PROFILE_LAB_CREDENTIAL_SOURCE_NOT_UNIQUE'}
   $source=$sources[0].Right
   if($source -is [System.Management.Automation.Language.PipelineAst] -and $source.PipelineElements.Count -eq 1) {
      $source=$source.PipelineElements[0]
   }
   # Support only Import-Clixml <literal path> for a user-bound DPAPI credential.
   if($source -is [System.Management.Automation.Language.CommandAst] -and
      $source.CommandElements.Count -eq 2 -and
      $source.CommandElements[0].Extent.Text -eq 'Import-Clixml' -and
      $source.CommandElements[1] -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
      $securePath=$source.CommandElements[1].Value
      $credential=Import-Clixml -LiteralPath $securePath -ErrorAction Stop
      if($credential -isnot [System.Management.Automation.PSCredential]){throw 'PROFILE_LAB_CREDENTIAL_TYPE_INVALID'}
      return $credential.GetNetworkCredential().Password
   }
   throw ('PROFILE_LAB_CREDENTIAL_SOURCE_UNSUPPORTED_' + $source.GetType().Name)
 }
 throw ('PROFILE_LAB_CONFIG_EXPRESSION_UNSUPPORTED_' + $rhs.GetType().Name)
}
$relay=Get-ProfileConfig 'EZSTUDIOLAB_ASSISTANT_BASE_URL'
if(-not $relay){$relay='http://EZSTUDIO-MAIN:8702'}
$token=Get-ProfileConfig 'EZSTUDIOLAB_ASSISTANT_TOKEN'
if (-not $relay -or -not $token) { throw 'PROFILE_RELOAD_LAB_TOKEN_UNAVAILABLE_IN_APPROVED_SOURCES' }
$uri=$null
if (-not [Uri]::TryCreate($relay,[UriKind]::Absolute,[ref]$uri) -or
 $uri.Scheme -notin @('http','https') -or -not $uri.Host -or $uri.UserInfo) {
 throw 'PROFILE_RELAY_URL_INVALID'
}

function Maintenance([string]$mode) {
 $suffix='/internal/analysis/desktop/profile/ai-requests/maintenance'
 
 $method=if($mode -eq 'status'){'GET'}else{'POST'}
 $args=@{Method=$method;Uri=($relay.TrimEnd('/')+$suffix);Headers=@{'X-EZScore-Analysis-Token'=$token};TimeoutSec=8}
 if($method -eq 'POST'){$args.ContentType='application/json';$args.Body=('{"mode":"'+$mode+'"}')}
 $v=Invoke-RestMethod @args
 if($v.ok -ne $true){throw "PROFILE_LAB_MAINTENANCE_FAILED:$mode"}
 return $v
}
function Processes([string]$path) {
 @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
  $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and
  $_.CommandLine.IndexOf($path,[StringComparison]::OrdinalIgnoreCase) -ge 0
 })
}
$paused=$false
$reloadSucceeded=$false
try {
 $v=Maintenance 'pause';$paused=$true
 if($v.maintenance -ne $true -or $v.active -ne $false){throw 'PROFILE_MAINTENANCE_NOT_IDLE'}
 $jobs=Invoke-RestMethod 'http://EZSTUDIO-MAIN:8700/api/jobs' -TimeoutSec 8
 if($jobs.ok -ne $true -or $null -eq $jobs.jobs -or $null -eq $jobs.queue_errors){throw 'ORCHESTRATOR_QUEUE_STATUS_UNVERIFIED'}
 if($jobs.queue_errors.PSObject.Properties.Name -contains 'lab_ai'){throw 'ORCHESTRATOR_PROFILE_QUEUE_UNREADABLE'}
 if(@($jobs.jobs | Where-Object {$_.kind -eq 'assistant.profile.review' -and $_.state -in @('running','claimed','cancelling')}).Count -gt 0){throw 'PROFILE_ACTIVE_JOB'}
 $g=@(Processes $guardianFile);$w=@(Processes $workerFile)
 if($g.Count -ne 1 -or $w.Count -ne 1){throw "PROFILE_PROCESS_COUNTS_INVALID guardian=$($g.Count) worker=$($w.Count)"}
 $old=$w[0]
 $check=Maintenance 'status'
 if($check.maintenance -ne $true -or $check.active -ne $false){throw 'PROFILE_RELOAD_LOST_MAINTENANCE'}
 $now=Get-CimInstance Win32_Process -Filter "ProcessId=$($old.ProcessId)"
 if($null -eq $now -or $now.CreationDate -ne $old.CreationDate -or $now.CommandLine.IndexOf($workerFile,[StringComparison]::OrdinalIgnoreCase) -lt 0){throw 'PROFILE_WORKER_PID_RACE'}
 Stop-Process -Id $old.ProcessId -ErrorAction Stop
 $until=(Get-Date).AddSeconds(45)
 do {
  Start-Sleep -Seconds 2
  $g=@(Processes $guardianFile);$w=@(Processes $workerFile)
  if($g.Count -ne 1 -or $w.Count -gt 1){throw 'PROFILE_GUARDIAN_OR_WORKER_DUPLICATED'}
  if($w.Count -eq 1 -and $w[0].ProcessId -ne $old.ProcessId){break}
 }while((Get-Date) -lt $until)
 if($w.Count -ne 1 -or $w[0].ProcessId -eq $old.ProcessId){throw 'PROFILE_GUARDIAN_RELOAD_TIMEOUT'}
 $reloadSucceeded=$true
 Write-Output "PROFILE_WORKER_RELOADED old=$($old.ProcessId) new=$($w[0].ProcessId)"
}finally{
 if($paused){
  $status=Maintenance 'status'
  if($reloadSucceeded -and $status.maintenance -eq $true -and $status.active -eq $false){
   [void](Maintenance 'resume')
   Write-Output 'PROFILE_QUEUE_RESUMED'
  }else{Write-Warning 'PROFILE_QUEUE_REMAINS_PAUSED_FOR_SAFETY'}
 }
}
