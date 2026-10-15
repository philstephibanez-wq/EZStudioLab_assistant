from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8-sig")

class V13FRuntimeHostResolutionContract(unittest.TestCase):
    def test_explicit_env_has_priority(self):
        self.assertIn('_explicit_host=os.getenv("EZSTUDIOLAB_HOST_REPO")', MAIN)
        self.assertIn("if _explicit_host:", MAIN)

    def test_single_root_runtime_is_supported(self):
        self.assertIn('(ASSISTANT_ROOT/"runtime"/"python").is_dir()', MAIN)
        self.assertIn('HOST_REPO=(ASSISTANT_ROOT/"runtime").resolve()', MAIN)

    def test_dev_sibling_lab_is_fallback(self):
        self.assertIn('HOST_REPO=(ASSISTANT_ROOT.parent/"EZStudio_lab").resolve()', MAIN)

    def test_legacy_parent_root_default_is_gone(self):
        self.assertNotIn(
            'Path(os.getenv("EZSTUDIOLAB_HOST_REPO",ASSISTANT_ROOT.parent))',
            MAIN,
        )

if __name__ == "__main__":
    unittest.main()
