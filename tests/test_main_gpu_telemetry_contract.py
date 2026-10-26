from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MainGpuTelemetryContract(unittest.TestCase):
    def test_web_container_is_gpu_unprivileged(self):
        compose = (ROOT / "docker/main/compose.yaml").read_text(encoding="utf-8")
        self.assertIn('EZSTUDIO_GPU_TELEMETRY_FILE: /run/ezstudio-gpu/telemetry.json', compose)
        self.assertIn('EZS_MAIN_GPU_TELEMETRY_DIR', compose)
        self.assertIn('target: /run/ezstudio-gpu', compose)
        self.assertIn('read_only: true', compose)
        self.assertNotIn('gpus: all', compose)
        self.assertNotIn('privileged: true', compose)

    def test_web_reads_shared_metrics_without_shell(self):
        controller = (ROOT / "src/Controller/GpuTelemetryController.php").read_text(encoding="utf-8")
        self.assertIn("gpu_telemetry_stale", controller)
        self.assertIn("EZSTUDIO_GPU_TELEMETRY_FILE", controller)
        self.assertNotIn("proc_open", controller)
        self.assertNotIn("nvidia-smi", controller)

    def test_host_exports_atomic_json(self):
        source = (ROOT / "scripts/main_gpu_telemetry.py").read_text(encoding="utf-8")
        self.assertIn("os.replace", source)
        self.assertIn("--query-gpu=", source)
        self.assertIn("capture_output=True", source)
        self.assertNotIn("shell=True", source)

if __name__ == "__main__":
    unittest.main()
