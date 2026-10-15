from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class V13FWebRuntimeSingleRootContract(unittest.TestCase):
    def test_web_runtime_is_inside_assistant_root(self):
        for name in ("start.ps1", "stop.ps1"):
            text = (ROOT / "scripts" / name).read_text(encoding="utf-8-sig")
            self.assertIn("$runtime = Join-Path $root 'runtime\\web'", text)
            self.assertNotIn("var\\assistant\\web", text)
            self.assertNotIn("$installRoot", text)

if __name__ == "__main__":
    unittest.main()
