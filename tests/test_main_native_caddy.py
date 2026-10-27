import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MainNativeCaddyContract(unittest.TestCase):
 def test_manual_caddy_and_gpu(self):
  code=(ROOT/"scripts/main-native-caddy.ps1").read_text(encoding="utf-8")
  for anchor in ("18812","18813","admin off","main-native-web.ps1","Get-OurCaddy","MAIN_NATIVE_CADDY_STOP_REFUSED","assistant/gpu/telemetry"):
   self.assertIn(anchor,code)
  self.assertNotIn("docker compose",code.lower())
  self.assertNotIn("Stop-Process -Name",code)
 def test_lab_gpu_projection_identical_except_route(self):
  code=(ROOT/"src/Controller/GpuTelemetryController.php").read_text(encoding="utf-8")
  self.assertIn("EZSTUDIO_NVIDIA_SMI",code)
  self.assertIn("memory_percent",code)
  self.assertIn("clocks.sm",code)
