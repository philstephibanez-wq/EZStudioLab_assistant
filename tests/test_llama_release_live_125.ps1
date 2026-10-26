$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script = [IO.File]::ReadAllText((Join-Path $root 'scripts\install-main.ps1'))
if ($script -notmatch 'if\(\$candidate\.draft\)\{continue\}') { throw 'DRAFT_FILTER_MISSING' }
if ($script -match '\$candidate\.prerelease') { throw 'OFFICIAL_BUILDS_EXCLUDED' }
$releases = @(Invoke-RestMethod -Uri 'https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=20' -Headers @{'User-Agent'='EZStudioLab-MAIN-CONTRACT'} -TimeoutSec 30)
$found = $null
foreach ($candidate in $releases) {
    if ($candidate.draft) { continue }
    $items = @($candidate.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-cpu-x64\.zip$' })
    if ($items.Count -eq 1) { $found = $items[0]; break }
}
if ($null -eq $found) { throw 'OFFICIAL_CPU_ASSET_NOT_FOUND' }
if ([string]$found.digest -notmatch '^sha256:[0-9a-fA-F]{64}$') { throw 'ASSET_SHA256_INVALID' }
Write-Output ('LLAMA_CPU_RELEASE_SELECTION_OK asset=' + $found.name)
