from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
s = (ROOT/'scripts'/'install-main.ps1').read_text(encoding='utf-8')
assert 'H:\\EZStudioLab_assistant' in s
assert 'Get-SmbShare -Name EZModels' in s
assert 'New-Item -ItemType Junction' in s
assert "if (-not $Apply)" in s
assert 'scripts\\start.ps1' in s
assert 'PROFILE_TOKEN_MISSING' in s
assert 'Copy-Item' in s
assert 'EZSTUDIOLAB_REVIEW_PRESET_PATH' in s
print('MAIN_BOOTSTRAP_STATIC_CONTRACT_OK')
