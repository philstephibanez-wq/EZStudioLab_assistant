"""Prevent retired host guidance from reappearing in active sources."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = (
    "README.md",
    "config/EZStudioLab_assistant.example.json",
    "app/profile_guardian.py",
    "app/profile_trace.py",
    "app/declarative_review.py",
    "app/profile_secret_reader.py",
    "templates/base.html.twig",
    "scripts/profile-runtime-diagnostic.ps1",
    "scripts/profile-ocr-translation-preflight.py",
    "scripts/profile-real-booklet-ocr.py",
    "scripts/profile-verify-readonly-diagnostic.py",
    "scripts/main-native-web.ps1",
    "app/profile_model_acquisition.py",
    "app/local_ai_runtime.py",
    "scripts/backfill_profile_trace_report.py",
)
RETIRED = ("scripts/start.cmd", "scripts/start.ps1",
           "scripts/stop.cmd", "scripts/stop.ps1")


class RetiredHostContract(unittest.TestCase):
    def test_no_retired_host_in_active_guidance(self):
        for rel in ACTIVE:
            with self.subTest(path=rel):
                self.assertNotIn("xps", (ROOT / rel).read_text(encoding="utf-8").casefold())

    def test_old_launchers_forbidden(self):
        for rel in RETIRED:
            with self.subTest(path=rel):
                self.assertFalse((ROOT / rel).exists())

    def test_current_lifecycle_script_present(self):
        self.assertTrue((ROOT / "scripts/assistant-lifecycle.ps1").is_file())


if __name__ == "__main__":
    unittest.main()
