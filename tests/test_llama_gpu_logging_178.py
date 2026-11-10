"""Durable non-regression checks for the Assistant Llama GPU logging contract."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PHP = ROOT / 'src' / 'Service' / 'AssistantLlamaLifecycle.php'

class LlamaGpuLogging178(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PHP.read_text(encoding='utf-8-sig')

    def test_trace_level_and_native_log(self):
        self.assertIn("--log-file \"'.$logFile.'\" -lv 4", self.source)
        self.assertIn("$this->log('LLAMA_NATIVE_LOG='.$logFile)", self.source)

    def test_canonical_gpu_guards_unchanged(self):
        self.assertIn("-ngl\\s+99", self.source)
        self.assertIn("Vulkan1", self.source)
        self.assertIn("--port\\s+8720", self.source)

    def test_no_shell_bootstrap_regression(self):
        self.assertIn("new \\COM('WScript.Shell')", self.source)
        self.assertIn('$shell->Run($line, 0, false);', self.source)
        self.assertIn("NATIVE_START_REQUESTED_WITHOUT_CONSOLE", self.source)

if __name__ == '__main__':
    unittest.main()
