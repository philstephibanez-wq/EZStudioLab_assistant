from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AssistantNativeLifecycle157(unittest.TestCase):
    def test_task_and_gpu_exclusive(self):
        s=(ROOT/'scripts/assistant-lifecycle.ps1').read_text(encoding='utf-8')
        self.assertIn('EZStudioLab Assistant Local AI',s)
        self.assertIn("-dev\\s+Vulkan1",s)
        self.assertIn('Start-ScheduledTask',s)
        self.assertIn('Stop-ScheduledTask',s)
        self.assertNotIn('Register-ScheduledTask',s)
        self.assertNotIn('Stop-Service',s)
        self.assertNotIn('host.docker.internal',s)
        self.assertIn('ASSISTANT_LLAMA_FOREIGN_EXECUTABLE',s)
    def test_intent_and_fail_closed(self):
        s=(ROOT/'scripts/assistant-lifecycle.ps1').read_text(encoding='utf-8')
        self.assertIn("Set-Intent 'STOPPED'",s)
        self.assertIn("Set-Intent 'RUNNING'",s)
        self.assertIn('ASSISTANT_INTENT_INVALID',s)
        self.assertIn('ASSISTANT_TASK_RUNNING_WITHOUT_LISTENER',s)
    def test_backoffice_and_probe_use_native(self):
        p=(ROOT/'src/Controller/MainBackofficeController.php').read_text(encoding='utf-8')
        j=(ROOT/'config/inference.main.json').read_text(encoding='utf-8')
        self.assertIn('http://127.0.0.1:8720/health',p)
        self.assertNotIn('host.docker.internal',p)
        self.assertIn('http://127.0.0.1:8720',j)
if __name__=='__main__':unittest.main()
