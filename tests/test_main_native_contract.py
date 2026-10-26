"""Native MAIN pilot remains isolated from Docker and XPS."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NativeMainContract(unittest.TestCase):
    def test_isolated_port_and_ownership(self):
        text=(ROOT/"scripts/main-native-web.ps1").read_text(encoding="utf-8")
        self.assertIn("$port = 18813",text)
        self.assertIn("Get-OurProcess",text)
        self.assertIn("MAIN_NATIVE_STOP_REFUSED",text)
        self.assertIn("Get-NetTCPConnection",text)
        self.assertNotIn("docker compose",text.lower())
        self.assertNotIn("Stop-Process -Name",text)
    def test_original_gpu_probe_unchanged(self):
        text=(ROOT/"src/Controller/GpuTelemetryController.php").read_text(encoding="utf-8")
        self.assertIn("EZSTUDIO_NVIDIA_SMI",text)
        self.assertIn("nvidia-smi",text)
        self.assertNotIn("EZSTUDIO_GPU_TELEMETRY_FILE",text)

if __name__ == "__main__":
    unittest.main()
