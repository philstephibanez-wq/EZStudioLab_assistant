from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AssistantNoLegacyStatusUi13D(unittest.TestCase):
    def test_version_is_13d(self):
        self.assertEqual(
            "1.3f",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_legacy_status_window_is_physically_removed(self):
        self.assertFalse((ROOT / "app" / "status_window.pyw").exists())

    def test_canonical_web_files_exist(self):
        self.assertTrue((ROOT / "public" / "index.php").is_file())
        self.assertTrue((ROOT / "scripts" / "start.cmd").is_file())
        self.assertTrue((ROOT / "scripts" / "start.ps1").is_file())
        self.assertTrue((ROOT / "scripts" / "stop.cmd").is_file())
        self.assertTrue((ROOT / "scripts" / "stop.ps1").is_file())

if __name__ == "__main__":
    unittest.main()

