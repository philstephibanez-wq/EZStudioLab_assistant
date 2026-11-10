"""Durable regression tests for llama.cpp startup instrumentation v1.7a7."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PHP = ROOT / 'src' / 'Service' / 'AssistantLlamaLifecycle.php'


class LlamaGpuLogging177(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.php = PHP.read_text(encoding='utf-8')

    def test_native_logging_persists_under_assistant_runtime(self):
        self.assertIn("assistant-llama-native-", self.php)
        self.assertIn("--log-file", self.php)
        self.assertIn("LLAMA_NATIVE_LOG=", self.php)
        self.assertIn("gmdate('Ymd_His')", self.php)

    def test_no_shell_wrapping_or_service_actions_added(self):
        self.assertIn("$shell->Run($line, 0, false);", self.php)
        self.assertIn('LLAMA_LOG_ARGUMENT_CONFLICT', self.php)
        self.assertIn('LLAMA_VERIFIED_PID_TERMINATED', self.php)
        self.assertIn('LLAMA_STOP_IDENTITY_MISMATCH', self.php)
        self.assertNotIn('cmd.exe /c', self.php)

    def test_new_logging_does_not_change_gpu_flags(self):
        self.assertIn('Vulkan1', self.php)
        self.assertIn('GPU_ARGUMENTS_MISMATCH', self.php)
        self.assertIn('GPU_CANONICAL_MODEL_INVALID', self.php)

    def test_version(self):
        self.assertEqual((ROOT / 'VERSION').read_text(encoding='utf-8').strip(), '1.7a7')


if __name__ == '__main__':
    unittest.main()
