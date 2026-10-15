from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AssistantWebSingletonV13C(unittest.TestCase):
    def test_version_is_13c(self):
        self.assertEqual("1.3f", (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_start_uses_atomic_singleton_lock(self):
        source = (ROOT / "scripts" / "start.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("instance.lock", source)
        self.assertIn("New-Item -ItemType Directory -Path $lockPath -ErrorAction Stop", source)
        self.assertIn("ASSISTANT_WEB_START_IN_PROGRESS_OR_RUNNING", source)
        self.assertIn("ASSISTANT_WEB_ALREADY_RUNNING", source)
        self.assertIn("assistant_web_partial_instance_detected", source)

    def test_start_rejects_port_conflicts(self):
        source = (ROOT / "scripts" / "start.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("Get-NetTCPConnection", source)
        self.assertIn("8712", source)
        self.assertIn("8713", source)
        self.assertIn("assistant_web_foreign_port_owner", source)
        self.assertIn("assistant_web_partial_instance_detected", source)
        self.assertIn("assistant_web_listener_validation_failed", source)

    def test_start_failure_releases_singleton(self):
        source = (ROOT / "scripts" / "start.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("Remove-Item -LiteralPath $lockPath -Recurse -Force", source)

    def test_stop_releases_singleton(self):
        source = (ROOT / "scripts" / "stop.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("instance.lock", source)
        self.assertIn("Remove-Item -LiteralPath $lockPath -Recurse -Force", source)


if __name__ == "__main__":
    unittest.main()


