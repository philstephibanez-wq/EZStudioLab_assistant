from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST_REPO = ROOT.parent / "EZStudio_lab"
MAIN = ROOT / "app" / "main.py"


class V11BImportIsolationContract(unittest.TestCase):
    def test_cli_uses_assistant_modules_before_host_python_root(self):
        env = os.environ.copy()
        env["EZSTUDIOLAB_HOST_REPO"] = str(HOST_REPO)

        proc = subprocess.run(
            [sys.executable, str(MAIN), "--help"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            proc.returncode,
            0,
            msg=f"stdout={proc.stdout}\nstderr={proc.stderr}",
        )
        self.assertIn("profile-review-queue", proc.stdout)
        self.assertNotIn("ImportError", proc.stderr)
        self.assertNotIn(str(HOST_REPO / "python" / "worker.py"), proc.stderr)


if __name__ == "__main__":
    unittest.main()
