from pathlib import Path
import unittest
class RuntimeCheckContract(unittest.TestCase):
 def test_diagnostic_read_only_and_no_secrets_output(self):
  content=(Path(__file__).resolve().parents[1]/"scripts/profile-runtime-diagnostic.ps1").read_text(encoding="utf-8")
  for text in ["PRESET_ENV_CONFIGURED","LAUNCHER_MENTIONS_PRESET_PATH","PROFILE_WORKER_COUNT","PROFILE_DIAGNOSTIC_READONLY_OK"]:
   self.assertIn(text,content)
  for cmd in ["Stop-Process","Stop-ScheduledTask","Start-ScheduledTask","GetNetworkCredential","Write-Output $path"]:
   self.assertNotIn(cmd,content)
