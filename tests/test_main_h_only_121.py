from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=(r/'scripts/install-main.ps1').read_text(encoding='utf-8')
w=(r/'runtime/profile_ai_requests_worker.py').read_text(encoding='utf-8')
assert "C:\\EZStudioLab_assistant" not in a
assert "C:\\EZStudioLab_assistant" not in w
assert "ROOT = Path(__file__).resolve().parents[1]" in w
assert "H:\\Caddy\\caddy.exe" in a
assert "Get-FileHash" in a and "LLAMA_SHA256_MISMATCH" in a
assert "H:\\temp" in a and "Get-SmbShare -Name EZModels" in a
assert "MAIN_INSTALL_READY" in a
print("MAIN_H_ONLY_CONTRACT_OK")
