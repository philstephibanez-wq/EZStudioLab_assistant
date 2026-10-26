# Installation MAIN pour le workflow canonique existant. PowerShell 5.1.
# Par defaut: controle sans modification. -Apply: prepare les dependances locales.
param(
    [switch]$Apply,
    [switch]$Start,
    [string]$LlamaServer = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$expectedRoot = 'H:\EZStudioLab_assistant'
$alias = 'C:\EZStudioLab_assistant'
$runtime = Join-Path $root 'runtime'
$launcher = Join-Path $runtime 'start_profile_ai_requests.ps1'
$exe = Join-Path $runtime 'ai\bin\llama-server.exe'
$modelRelative = 'assistant\bench\qwen2.5-1.5b-instruct-q4_k_m'
$modelName = 'qwen2.5-1.5b-instruct-q4_k_m.gguf'
$modelLink = Join-Path $runtime ('models-cache\' + $modelRelative)
$modelFile = Join-Path $modelLink $modelName
$share = Get-SmbShare -Name EZModels -ErrorAction Stop
$modelPhysical = Join-Path $share.Path $modelRelative
$modelSource = Join-Path $modelPhysical $modelName
function Assert-DirTarget([string]$link, [string]$target) {
    if (-not (Test-Path -LiteralPath $link)) { return $false }
    $item = Get-Item -LiteralPath $link -Force
    if (-not $item.LinkType -or @($item.Target).Count -ne 1 -or
        -not [string]::Equals([string](@($item.Target)[0]), $target, [StringComparison]::OrdinalIgnoreCase)) {
        throw "LINK_CONFLICT:$link"
    }
    return $true
}
function Assert-FreePort([int]$port) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "PORT_OCCUPIED:$port"
    }
}
function Report([string]$name, [bool]$ok) {
    Write-Output ("{0}={1}" -f $name, $(if($ok){'OK'}else{'MISSING'}))
}
if (-not [string]::Equals($root,$expectedRoot,[StringComparison]::OrdinalIgnoreCase)) {
    throw "ROOT_UNEXPECTED:$root"
}
if (-not (Test-Path -LiteralPath $modelSource -PathType Leaf)) { throw "MODEL_SOURCE_MISSING:$modelSource" }
if (-not (Test-Path -LiteralPath (Join-Path $root 'vendor\autoload_runtime.php'))) { throw 'COMPOSER_VENDOR_MISSING' }
if (-not (Test-Path -LiteralPath (Join-Path $root '.env.local'))) { throw 'ENV_LOCAL_MISSING' }
$python = 'C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_MISSING' }
$caddy = if (Test-Path 'C:\Caddy\caddy.exe') { 'C:\Caddy\caddy.exe' } else {
    $command = Get-Command caddy.exe -ErrorAction SilentlyContinue
    if ($command) { $command.Source } else { '' }
}
if (-not $caddy) { throw 'CADDY_MISSING:installer Caddy avant -Apply' }
if (-not (Get-Command php.exe -ErrorAction SilentlyContinue)) { throw 'PHP_MISSING' }
if ($LlamaServer -and -not (Test-Path -LiteralPath $LlamaServer -PathType Leaf)) {
    throw 'LLAMA_SERVER_SOURCE_MISSING'
}
$aliasOk = Assert-DirTarget $alias $root
$linkOk = Assert-DirTarget $modelLink $modelPhysical
Report 'MAIN_ALIAS' $aliasOk
Report 'MODEL_LINK' $linkOk
Report 'LLAMA_SERVER' (Test-Path -LiteralPath $exe -PathType Leaf)
Report 'PROFILE_LAUNCHER' (Test-Path -LiteralPath $launcher -PathType Leaf)
if (-not $Apply) {
    Write-Output 'PREFLIGHT_READ_ONLY_OK'
    exit 0
}
foreach ($port in @(8712,8713,8720)) { Assert-FreePort $port }
if (-not $aliasOk) {
    New-Item -ItemType Junction -Path $alias -Target $root -ErrorAction Stop | Out-Null
}
if (-not $linkOk) {
    $parent = Split-Path -Parent $modelLink
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    New-Item -ItemType Junction -Path $modelLink -Target $modelPhysical -ErrorAction Stop | Out-Null
}
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    if (-not $LlamaServer) { throw 'LLAMA_SERVER_REQUIRED: fournir -LlamaServer vers executable EXISTANT' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $exe) -Force | Out-Null
    Copy-Item -LiteralPath $LlamaServer -Destination $exe -ErrorAction Stop
    # Attention: distribuer aussi les DLL associees si necessaires; ne pas supprimer le source.
    Get-ChildItem -LiteralPath (Split-Path -Parent $LlamaServer) -Filter '*.dll' -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path (Split-Path -Parent $exe) $_.Name) -ErrorAction Stop
    }
}
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    $contents = @'
$ErrorActionPreference = 'Stop'
$root = 'H:\EZStudioLab_assistant'
$envPath = Join-Path $root '.env.local'
# Charger seulement les cles necessaires, sans evaluer le fichier et sans les afficher.
foreach ($line in [IO.File]::ReadAllLines($envPath)) {
    if ($line -match '^\s*(EZSTUDIOLAB_ASSISTANT_TOKEN|EZSTUDIOLAB_ASSISTANT_BASE_URL|EZSTUDIOLAB_REVIEW_PRESET_PATH)\s*=\s*(.*)\s*$') {
        $key = $matches[1]
        $value = $matches[2].Trim()
        if ($value.Length -ge 2 -and (($value[0] -eq '"' -and $value[-1] -eq '"') -or
             ($value[0] -eq "'" -and $value[-1] -eq "'"))) {
            $value = $value.Substring(1,$value.Length-2)
        }
        [Environment]::SetEnvironmentVariable($key,$value,'Process')
    }
}
if (-not $env:EZSTUDIOLAB_ASSISTANT_TOKEN) { throw 'PROFILE_TOKEN_MISSING: config locale' }
if (-not $env:EZSTUDIOLAB_REVIEW_PRESET_PATH) { throw 'PROFILE_PRESET_PATH_MISSING: config locale' }
$python = 'C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
& $python -u (Join-Path $root 'runtime\profile_ai_requests_worker.py')
exit $LASTEXITCODE
'@
    [IO.File]::WriteAllText($launcher,$contents,(New-Object System.Text.UTF8Encoding($false)))
}
if (-not (Test-Path -LiteralPath $modelFile -PathType Leaf)) { throw 'MODEL_LINK_INVALID' }
Write-Output 'MAIN_PREPARED: execution non demarree'
if ($Start) {
    # Etablir le token et le preset pour le process guardian, sans jamais les afficher.
    $local = [IO.File]::ReadAllLines((Join-Path $root '.env.local'))
    foreach ($line in $local) {
        if ($line -match '^\s*(EZSTUDIOLAB_ASSISTANT_TOKEN|EZSTUDIOLAB_ASSISTANT_BASE_URL|EZSTUDIOLAB_REVIEW_PRESET_PATH)\s*=\s*(.*)\s*$') {
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($matches[1],$value,'Process')
        }
    }
    if (-not $env:EZSTUDIOLAB_ASSISTANT_TOKEN) { throw 'PROFILE_TOKEN_MISSING' }
    if (-not $env:EZSTUDIOLAB_REVIEW_PRESET_PATH) { throw 'PROFILE_PRESET_PATH_MISSING' }
    & (Join-Path $root 'scripts\start.ps1')
    if (-not $?) { throw 'CANONICAL_START_FAILED' }
}
