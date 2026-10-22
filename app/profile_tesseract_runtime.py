"""Locate OCR binary on XPS and tessdata models over MAIN SMB; never copy models."""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

DEFAULT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DEFAULT_TESSDATA = r"\\EZSTUDIO-MAIN\EZModels\tesseract\tessdata_best"


def resolve_tesseract():
    """Fail closed when a required model is missing or the share is inaccessible."""
    exe = os.environ.get("EZS_TESSERACT_EXE") or shutil.which("tesseract") or DEFAULT_EXE
    if not Path(exe).is_file():
        return {"status": "executable_missing"}
    data_path = os.environ.get("EZS_TESSDATA_DIR") or DEFAULT_TESSDATA
    data = Path(data_path)
    if not (data / "eng.traineddata").is_file():
        return {"status": "english_model_unavailable", "tessdata_dir": data_path}
    if not (data / "fra.traineddata").is_file():
        return {"status": "french_model_unavailable", "tessdata_dir": data_path}
    env = os.environ.copy()
    # - -tessdata-dir explicitly sets model location in Tesseract 5.
    try:
        result = subprocess.run([str(exe), "--list-langs", "--tessdata-dir", str(data)],
                                capture_output=True, text=True, timeout=10, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "models_unreadable", "tessdata_dir": data_path}
    if result.returncode != 0 or not {"eng", "fra"}.issubset(set(result.stdout.splitlines())):
        return {"status": "models_unreadable", "tessdata_dir": data_path}
    return {"status": "ready", "executable": str(exe), "tessdata_dir": str(data)}
