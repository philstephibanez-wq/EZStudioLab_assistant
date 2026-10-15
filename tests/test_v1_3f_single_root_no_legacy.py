from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class V13FSingleRootNoLegacyContract(unittest.TestCase):
    def test_version(self):
        self.assertEqual(
            "1.3h",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_legacy_python_ui_removed(self):
        self.assertFalse((ROOT / "app" / "status_window.pyw").exists())
        self.assertFalse((ROOT / "tests" / "test_v1d_local_status_window.py").exists())

    def test_legacy_launcher_removed(self):
        self.assertFalse(
            (ROOT / "scripts" / "start-EZStudioLab_assistant.ps1").exists()
        )

    def test_canonical_lifecycle_only(self):
        for rel in (
            "scripts/start.cmd",
            "scripts/start.ps1",
            "scripts/stop.cmd",
            "scripts/stop.ps1",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_runtime_dirs_are_git_ignored(self):
        lines = set(
            (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        )
        self.assertIn("/runtime/", lines)
        self.assertIn("/logs/", lines)
        self.assertIn("/models/", lines)

    def test_no_legacy_runtime_sibling_literal_in_product_source(self):
        forbidden = "EZStudioLab_" + "assistant_runtime"
        for base in ("app", "scripts", "public", "src", "templates"):
            path = ROOT / base
            if not path.exists():
                continue
            for p in path.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in {
                    ".py", ".ps1", ".cmd", ".php", ".twig", ".js", ".json", ".md"
                }:
                    continue
                source = p.read_text(encoding="utf-8-sig", errors="strict")
                self.assertNotIn(forbidden, source, str(p))


if __name__ == "__main__":
    unittest.main()
