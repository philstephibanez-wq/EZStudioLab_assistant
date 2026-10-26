# MAIN: installation contrôlée sur H:, PowerShell 5.1.
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
$share=Get-SmbShare -Name EZModels -ErrorAction Stop
$modelPhysical=Join-Path $share.Path $modelRelative
if (-not (Test-Path -LiteralPath (Join-Path $modelPhysical $modelName) -PathType Leaf)) { throw 'QWEN_MODEL_MISSING' }
if (-not (Test-Path -LiteralPath 'H:\Caddy\caddy.exe' -PathType Leaf)) { throw 'SHARED_CADDY_MISSING' }
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
$exeOK=Test-Path -LiteralPath $exe -PathType Leaf
$launcherOK=Test-Path -LiteralPath $launcher -PathType Leaf
Write-Output "MODEL_LINK=$linkOK LLAMA_SERVER=$exeOK PROFILE_LAUNCHER=$launcherOK"
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
if(-not $exeOK){
    # Official GitHub release API; install only verified win-cpu-x64 ZIP in disposable H:\temp.
    $releases=Invoke-RestMethod -Uri 'https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=20' -Headers @{'User-Agent'='EZStudioLab-MAIN'} -TimeoutSec 30
    $release=$null
    $asset=$null
    foreach($candidate in $releases){
        if($candidate.draft){continue}
        $items=@($candidate.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-cpu-x64\.zip$' })
        if($items.Count -eq 1){$release=$candidate; $asset=$items[0]; break}
    }
    if($null -eq $asset){throw 'LLAMA_CPU_X64_RELEASE_NOT_FOUND'}
    if([string]$asset.digest -notmatch '^sha256:([0-9a-fA-F]{64})$'){throw 'LLAMA_RELEASE_SHA256_MISSING'}
    $sha=$matches[1].ToLowerInvariant()
    $stage=Join-Path 'H:\temp' ('EZStudio_Llama_' + [string]$release.tag_name)
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    $zip=Join-Path $stage $asset.name
    if(-not (Test-Path -LiteralPath $zip -PathType Leaf)){
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing -TimeoutSec 600
    }
    if((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha){throw 'LLAMA_SHA256_MISMATCH'}
    $unpack=Join-Path $stage 'unpacked'
    if(-not (Test-Path -LiteralPath $unpack -PathType Container)){
        Expand-Archive -LiteralPath $zip -DestinationPath $unpack -ErrorAction Stop
    }
    $matchesExe=@(Get-ChildItem -LiteralPath $unpack -Recurse -Filter 'llama-server.exe' -File)
    if($matchesExe.Count -ne 1){throw 'LLAMA_EXE_NOT_UNIQUE'}
    $sourceDir=$matchesExe[0].DirectoryName
    $destination=Split-Path -Parent $exe
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    # Runtime distribution exe + sibling DLLs, never models.
    Copy-Item -LiteralPath $matchesExe[0].FullName -Destination $exe -ErrorAction Stop
    Get-ChildItem -LiteralPath $sourceDir -Filter '*.dll' -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destination $_.Name) -ErrorAction Stop
    }
    Write-Output ('LLAMA_INSTALLED_SHA256_VERIFIED release='+$release.tag_name)
}
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
if($Start){
    foreach($k in $local.Keys){[Environment]::SetEnvironmentVariable($k,$local[$k],'Process')}
    & (Join-Path $root 'scripts\start.ps1')
    if(-not $?){throw 'MAIN_START_FAILED'}
}
