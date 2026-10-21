# Read-only preflight using the already-configured local PROFILE launcher. Does not execute it.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$launcher = Join-Path $root 'runtime\start_profile_ai_requests.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'PROFILE_LAUNCHER_MISSING' }
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$errors)
if (@($errors).Count -gt 0) { throw 'PROFILE_LAUNCHER_PARSE_ERROR' }
$assignments = @($ast.FindAll({
  param($node)
  $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
  $node.Left.Extent.Text -ieq '$env:EZSTUDIOLAB_REVIEW_PRESET_PATH'
}, $true))
if ($assignments.Count -ne 1) { throw ('PROFILE_PRESET_ASSIGNMENT_COUNT=' + $assignments.Count) }
$rhs = $assignments[0].Right
if ($rhs -is [System.Management.Automation.Language.CommandExpressionAst]) { $rhs = $rhs.Expression }
if ($rhs -isnot [System.Management.Automation.Language.StringConstantExpressionAst]) {
  throw 'PROFILE_PRESET_ASSIGNMENT_NOT_LITERAL'
}
$path = $rhs.Value
if (-not $path.StartsWith('\\')) { throw 'PROFILE_PRESET_NOT_UNC' }
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'PROFILE_PRESET_INACCESSIBLE' }
$env:EZSTUDIOLAB_REVIEW_PRESET_PATH = $path
try {
  & python (Join-Path $root 'scripts\preflight_profile_15a.py')
  if ($LASTEXITCODE -ne 0) { throw ('PROFILE_PREFLIGHT_FAILED=' + $LASTEXITCODE) }
} finally {
  Remove-Item Env:EZSTUDIOLAB_REVIEW_PRESET_PATH -ErrorAction SilentlyContinue
}
