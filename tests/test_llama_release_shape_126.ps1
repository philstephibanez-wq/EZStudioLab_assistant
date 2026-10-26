$ErrorActionPreference = 'Stop'
$path = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts\install-main.ps1'
$source = [IO.File]::ReadAllText($path)
if ($source -match '\$releases\s*=\s*@\(\s*Invoke-RestMethod') { throw 'API_ARRAY_NESTED' }
$errors = $null
$tokens = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
if (@($errors).Count -ne 0) { throw 'BOOTSTRAP_PARSE_FAILED' }
# Imitate the Windows PowerShell 5.1 API response as an already-materialized array.
$fixture = @(
    [pscustomobject]@{tag_name='b1234';draft=$false;assets=@([pscustomobject]@{name='llama-b1234-bin-win-cpu-x64.zip';digest='sha256:' + ('a' * 64)})},
    [pscustomobject]@{tag_name='b1233';draft=$false;assets=@()}
)
$found = $null
foreach($candidate in $fixture){
    if($candidate.draft){continue}
    $items=@($candidate.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-cpu-x64\.zip$' })
    if($items.Count -eq 1){$found=$items[0];break}
}
if($null -eq $found -or $found.name -ne 'llama-b1234-bin-win-cpu-x64.zip'){throw 'RELEASE_SELECTOR_FIXTURE_FAILED'}
Write-Output 'LLAMA_RELEASE_SHAPE_CONTRACT_OK'
