# Analyse de syntaxe PowerShell 5.1 sans execution de l'installateur.
$ErrorActionPreference = 'Stop'
$path = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts\install-main.ps1'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
if (@($errors).Count -ne 0) {
    foreach ($item in $errors) { Write-Error ("PS_PARSE_ERROR line={0} message={1}" -f $item.Extent.StartLineNumber, $item.Message) }
    throw 'MAIN_INSTALL_POWERSHELL_PARSE_FAILED'
}
$source = [IO.File]::ReadAllText($path)
if ([regex]::Matches($source, 'LLAMA_CPU_X64_RELEASE_NOT_FOUND').Count -ne 1) { throw 'RELEASE_SELECT_BLOCK_DUPLICATE' }
if ([regex]::Matches($source, 'MAIN_INSTALL_READY').Count -ne 1) { throw 'MAIN_INSTALL_BLOCK_DUPLICATE' }
if ($source -notmatch 'llama-b\[0-9\]\+-bin-win-cpu-x64') { throw 'LLAMA_SELECTOR_MISSING' }
Write-Output 'MAIN_INSTALL_POWERSHELL_PARSE_OK'
