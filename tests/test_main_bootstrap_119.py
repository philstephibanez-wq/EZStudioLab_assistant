"""Validation de non regression des preconditions et operations du bootstrap MAIN."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = (ROOT / 'scripts' / 'install-main.ps1').read_text(encoding='utf-8')
assert 'H:\\EZStudioLab_assistant' in s
assert 'Get-SmbShare -Name EZModels' in s
assert 'New-Item -ItemType Junction' in s
assert "if (-not $Apply)" in s
assert 'EZSTUDIOLAB_ASSISTANT_TOKEN' in s
assert 'EZSTUDIOLAB_REVIEW_PRESET_PATH' in s
assert 'runtime\\profile_ai_requests_worker.py' in s
assert 'GPU_LLAMA_RUNTIME_MISSING_NO_CPU_FALLBACK' in s
assert 'LEGACY_MAIN_START_UNSUPPORTED_USE_ASSISTANT_EXISTING_LIFECYCLE' in s
assert 'win-cpu-x64' not in s
print('MAIN_BOOTSTRAP_GPU_CONTRACT_OK')
