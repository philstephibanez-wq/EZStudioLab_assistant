"""Durable tests for strict GPU device selection, no service or model start."""
import pathlib, re, subprocess, unittest, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PHP = ROOT / 'src/Service/AssistantLlamaLifecycle.php'

class GpuDevice179(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PHP.read_text(encoding='utf-8')

    def test_dynamic_selector_invoked_before_start(self):
        s = self.source
        self.assertIn('$args = $this->resolveNvidiaDevice($exe, $args);', s)
        self.assertLess(s.index('$args = $this->resolveNvidiaDevice($exe, $args);'), s.index('$shell->Run($line, 0, false);'))
        self.assertIn("['bypass_shell' => true, 'create_new_console' => false]", s)
        self.assertIn("$deadline = microtime(true) + 10.0",s)

    def test_canonical_gpu_arguments_retained(self):
        s=self.source
        for marker in ('-ngl\\s+99', '-c\\s+4096', '127\\.0\\.0\\.1', '8720', 'GPU_CANONICAL_MODEL_INVALID'):
            self.assertIn(marker,s)
        self.assertIn("'-dev '.$device",s)
        self.assertIn('LLAMA_GPU_SELECTED=',s)
        self.assertIn("--log-file",s)
        self.assertIn("-lv 4",s)

    def test_stop_identity_supports_both_indices(self):
        self.assertIn('Vulkan[0-9]+',self.source)
        self.assertIn('LLAMA_STOP_IDENTITY_MISMATCH',self.source)
        self.assertIn('LLAMA_STOP_PID_REUSED',self.source)
        self.assertIn('hasConfiguredLocalModel',self.source)

    def test_nvidia_matching_both_orders_and_fail_closed(self):
        php=shutil.which('php')
        if php is None:self.skipTest('PHP executable unavailable')
        code='''require $argv[1];
$m = new ReflectionMethod('App\\Service\\AssistantLlamaLifecycle','nvidiaDeviceFromList');
try { echo $m->invoke(null,base64_decode($argv[2])); }
catch (Throwable $e) { fwrite(STDERR,$e->getMessage()); exit(4); }'''
        samples=[
            ('Available devices:\n Vulkan0: Intel(R) UHD Graphics 630 (8098 MiB)\n Vulkan1: NVIDIA GeForce RTX 2060 (6169 MiB)\n', 'Vulkan1'),
            ('Available devices:\n Vulkan0: NVIDIA GeForce RTX 2060 (6169 MiB)\n Vulkan1: Intel(R) UHD Graphics 630 (8098 MiB)\n','Vulkan0'),
            ('Available devices:\n Vulkan0: Intel(R) UHD Graphics 630 (8098 MiB)\n',None),
            (' Vulkan0: NVIDIA GeForce RTX 2060 (6169 MiB)\n Vulkan1: NVIDIA GeForce RTX 2060 (6169 MiB)\n',None),
            (' Vulkan0: NVIDIA GeForce RTX 2060 (6169 MiB)\n Vulkan0: NVIDIA GeForce RTX 2060 (6169 MiB)\n',None),
        ]
        import base64
        for sample,expected in samples:
            with self.subTest(expected=expected):
                cp=subprocess.run([php,'-r',code,str(PHP),base64.b64encode(sample.encode()).decode()], capture_output=True,text=True,timeout=10)
                if expected:
                    self.assertEqual(cp.returncode,0,cp.stderr)
                    self.assertEqual(cp.stdout,expected)
                else:
                    self.assertNotEqual(cp.returncode,0)
                    self.assertIn('LLAMA_NVIDIA_DEVICE_NOT_UNIQUE_OR_MISSING',cp.stderr)

if __name__=='__main__':unittest.main()
