from pathlib import Path
s=(Path(__file__).resolve().parents[1]/'scripts/install-main.ps1').read_text(encoding='utf-8')
assert 'releases?per_page=20' in s
assert "if($candidate.draft -or $candidate.prerelease)" in s
assert "llama-b[0-9]+-bin-win-cpu-x64" in s
assert "LLAMA_CPU_X64_RELEASE_NOT_FOUND" in s
assert "LLAMA_RELEASE_SHA256_MISSING" in s and 'LLAMA_SHA256_MISMATCH' in s
print("LLAMA_RELEASE_SELECTOR_STATIC_OK")
