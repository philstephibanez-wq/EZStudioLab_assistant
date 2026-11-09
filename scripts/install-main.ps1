# MAIN: installation controlee sur H:, PowerShell 5.1.
# 1.6a(156): le runtime IA GPU natif est gere par l'Assistant ; jamais de CPU implicite.
param([switch]$Apply,[switch]$Start)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not [string]::Equals($root,'H:\EZStudioLab_assistant',[StringComparison]::OrdinalIgnoreCase)) { throw "ROOT_UNEXPECTED:$root" }
$runtime=Join-Path $root 'runtime'
$exe=Join-Path $runtime 'ai\bin\llama-server.exe'
$modelRelative='assistant\bench\qwen2.5-1.5b-instruct-q4_k_m'
$modelLink=Join-Path $runtime ('models-cache\'+$modelRelative)
$modelName='qwen2.5-1.5b-instruct-q4_k_m.gguf'
$launcher=Join-Path $runtime 'start_profile_ai_requests.ps1'
# Ancienne option de boot retiree : ne jamais invoquer scripts/start.ps1 (supprime en 1.6a(155)).
# Cette installation ne demarre ni Web, ni Llama, ni tache Windows.
if($Start){throw 'LEGACY_MAIN_START_UNSUPPORTED_USE_ASSISTANT_EXISTING_LIFECYCLE'}
# Interdiction de toute acquisition implicite de binaire, meme quand -Apply est demande.
if(-not (Test-Path -LiteralPath $exe -PathType Leaf)){throw 'GPU_LLAMA_RUNTIME_MISSING_NO_CPU_FALLBACK'}
$devices = @(& $exe --list-devices 2>&1)
if($LASTEXITCODE -ne 0 -or (($devices -join "`n") -notmatch 'Vulkan1:\s*NVIDIA GeForce RTX 2060')){
    throw 'GPU_LLAMA_VULKAN1_RTX2060_NOT_VERIFIED_NO_CPU_FALLBACK'
}
$share=Get-SmbShare -Name EZModels -ErrorAction Stop
$modelPhysical=Join-Path $share.Path $modelRelative
if (-not (Test-Path -LiteralPath (Join-Path $modelPhysical $modelName) -PathType Leaf)) { throw 'QWEN_MODEL_MISSING' }
# FrankenPHP est le seul hote Web; aucun preflight ni demarrage Caddy.
if (-not (Test-Path -LiteralPath (Join-Path $root 'vendor\autoload_runtime.php'))) { throw 'VENDOR_MISSING' }
if (-not (Test-Path -LiteralPath (Join-Path $root '.env.local'))) { throw 'ENV_LOCAL_MISSING' }
$python='C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_MISSING' }
function Test-ExpectedJunction([string]$Path,[string]$Target) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $i=Get-Item -LiteralPath $Path -Force
    if ($i.LinkType -ne 'Junction' -or @($i.Target).Count -ne 1 -or
        -not [string]::Equals([string](@($i.Target)[0]),$Target,[StringComparison]::OrdinalIgnoreCase)) { throw "EXISTING_PATH_CONFLICT:$Path" }
    return $true
}
$linkOK=Test-ExpectedJunction $modelLink $modelPhysical
$launcherOK=Test-Path -LiteralPath $launcher -PathType Leaf
Write-Output "MODEL_LINK=$linkOK LLAMA_GPU_VULKAN1_VERIFIED=True PROFILE_LAUNCHER=$launcherOK"
if (-not $Apply) { Write-Output 'MAIN_PREFLIGHT_READ_ONLY_OK'; exit 0 }
foreach($port in @(8712,8713,8720,2022)){
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "PORT_OCCUPIED:$port" }
}
# Validation du secret sans divulgation
$required=@('EZSTUDIOLAB_ASSISTANT_TOKEN')
$mainPreset='H:\EZStudio_lab\presets\assistant\profile-baseline-1.json'
$local=@{}
foreach($line in [IO.File]::ReadAllLines((Join-Path $root '.env.local'))){
    if($line -match '^\s*(EZSTUDIOLAB_ASSISTANT_TOKEN|EZSTUDIOLAB_ASSISTANT_BASE_URL|EZSTUDIOLAB_REVIEW_PRESET_PATH)\s*=\s*(.*)$'){
        $v=$matches[2].Trim()
        if($v.Length -gt 1 -and (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'")))){$v=$v.Substring(1,$v.Length-2)}
        $local[$matches[1]]=$v
    }
}
foreach($key in $required){if(-not $local.ContainsKey($key) -or -not $local[$key]){throw "LOCAL_CONFIG_REQUIRED:$key"}}
if(-not $local.ContainsKey('EZSTUDIOLAB_REVIEW_PRESET_PATH') -or -not $local['EZSTUDIOLAB_REVIEW_PRESET_PATH']){$local['EZSTUDIOLAB_REVIEW_PRESET_PATH']=$mainPreset}
if(-not (Test-Path -LiteralPath $local['EZSTUDIOLAB_REVIEW_PRESET_PATH'] -PathType Leaf)){throw 'REVIEW_PRESET_MISSING'}
if(-not $linkOK){
    New-Item -ItemType Directory -Path (Split-Path -Parent $modelLink) -Force | Out-Null
    New-Item -ItemType Junction -Path $modelLink -Target $modelPhysical | Out-Null
}
if(-not $launcherOK){
    $content=@'
$ErrorActionPreference='Stop'
$root='H:\EZStudioLab_assistant'
foreach($line in [IO.File]::ReadAllLines((Join-Path $root '.env.local'))){
    if($line -match '^\s*(EZSTUDIOLAB_ASSISTANT_TOKEN|EZSTUDIOLAB_ASSISTANT_BASE_URL|EZSTUDIOLAB_REVIEW_PRESET_PATH)\s*=\s*(.*)$'){
        $value=$matches[2].Trim()
        if($value.Length -gt 1 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))){$value=$value.Substring(1,$value.Length-2)}
        [Environment]::SetEnvironmentVariable($matches[1],$value,'Process')
    }
}
if(-not $env:EZSTUDIOLAB_ASSISTANT_TOKEN){throw 'TOKEN_MISSING'}
if(-not $env:EZSTUDIOLAB_REVIEW_PRESET_PATH){$env:EZSTUDIOLAB_REVIEW_PRESET_PATH='H:\EZStudio_lab\presets\assistant\profile-baseline-1.json'}
$python='C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe'
& $python -u (Join-Path $root 'runtime\profile_ai_requests_worker.py')
exit $LASTEXITCODE
'@
    [IO.File]::WriteAllText($launcher,$content,(New-Object System.Text.UTF8Encoding($false)))
}
Write-Output 'MAIN_INSTALL_READY'
