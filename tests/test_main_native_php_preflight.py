"""Regression: don't close the PHP -v output pipe before inspecting its exit code."""
import unittest
from pathlib import Path

class NativePhpPreflightTests(unittest.TestCase):
    def test_complete_php_version_process_before_exit_check(self):
        script=(Path(__file__).resolve().parents[1]/"scripts/main-native-web.ps1").read_text(encoding="utf-8")
        self.assertIn("$phpVersionLines = @(& $binary -v)",script)
        self.assertIn("$phpExitCode = $LASTEXITCODE",script)
        self.assertIn("if ($phpExitCode -ne 0 -or $phpVersionLines.Count -eq 0)",script)
        self.assertNotIn("& $binary -v | Select-Object -First 1",script)

if __name__ == "__main__":
    unittest.main()
