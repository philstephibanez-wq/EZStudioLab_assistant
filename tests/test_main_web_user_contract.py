"""Contract: Symfony smoke runs as tmpfs owner without elevated capabilities."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WebUserContract(unittest.TestCase):
    def test_web_runs_as_tmpfs_owner(self):
        data = (ROOT / "docker/main/compose.yaml").read_text(encoding="utf-8")
        self.assertIn('    user: "33:33"', data)
        self.assertIn('/opt/ezstudio-assistant/var:uid=33,gid=33', data)
        self.assertIn('    read_only: true', data)
        self.assertIn('      - no-new-privileges:true', data)
        self.assertIn('      - ALL', data)
        self.assertNotIn("privileged: true", data)
        self.assertNotIn("gpus: all", data)
        self.assertNotIn("EZSTUDIO_GPU_TELEMETRY_FILE", data)

if __name__ == "__main__":
    unittest.main()
