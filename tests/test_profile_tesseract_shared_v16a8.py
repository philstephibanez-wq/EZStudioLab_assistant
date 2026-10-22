import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_tesseract_runtime import resolve_tesseract


class SharedTessdata(unittest.TestCase):
    def test_missing_executable_abstains(self):
        with patch.dict(os.environ, {"EZS_TESSERACT_EXE": "/definitely/not/installed/tesseract"}):
            self.assertEqual(resolve_tesseract()["status"], "executable_missing")

    def test_missing_french_model_abstains_without_model_copy(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "tesseract.exe"
            exe.write_bytes(b"")
            (Path(d) / "eng.traineddata").write_bytes(b"example")
            with patch.dict(os.environ, {"EZS_TESSERACT_EXE": str(exe),
                                         "EZS_TESSDATA_DIR": d}):
                result = resolve_tesseract()
            self.assertEqual(result["status"], "french_model_unavailable")

    def test_both_files_present_requires_binary_readability(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "tesseract.exe"
            exe.write_bytes(b"")
            for lang in ("eng", "fra"):
                (Path(d) / (lang + ".traineddata")).write_bytes(b"example")
            with patch.dict(os.environ, {"EZS_TESSERACT_EXE": str(exe),
                                         "EZS_TESSDATA_DIR": d}):
                result = resolve_tesseract()
            self.assertEqual(result["status"], "models_unreadable")


if __name__ == "__main__":
    unittest.main()
