from pathlib import Path
r=Path(__file__).resolve().parents[1]
d=(r/'app/declarative_review.py').read_text(encoding='utf-8')
s=(r/'scripts/install-main.ps1').read_text(encoding='utf-8')
assert "profile-baseline-1.json" in d and "normcase" in d
assert "review_preset_requires_main_unc_or_local_canonical_path" in d
assert "$mainPreset='H:\\EZStudio_lab\\presets\\assistant\\profile-baseline-1.json'" in s
assert "EZSTUDIOLAB_ASSISTANT_TOKEN" in s
assert "REVIEW_PRESET_MISSING" in s
print("MAIN_LOCAL_PRESET_STATIC_OK")
