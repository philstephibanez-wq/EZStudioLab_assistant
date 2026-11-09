import pathlib
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
class AssistantAutoStart158(unittest.TestCase):
    def test_one_shot_and_gpu_task_only(self):
        text=(ROOT/'scripts/ai-auto-bootstrap.ps1').read_text(encoding='utf-8')
        self.assertIn("Start-ScheduledTask -TaskName $taskName",text)
        self.assertIn('Vulkan1',text)
        self.assertIn('SKIP_EXPLICIT_STOPPED',text)
        self.assertNotIn('Start-Service',text)
        self.assertNotIn('Stop-Service',text)
        self.assertNotIn('Stop-Process',text)
    def test_trigger_owned_by_assistant(self):
        text=(ROOT/'scripts/install-ai-autostart.ps1').read_text(encoding='utf-8')
        self.assertIn('EventTrigger',text)
        self.assertIn('LogonTrigger',text)
        self.assertIn('EZS_FrankenPHP',text)
        self.assertIn('EZStudioLab Assistant AI Bootstrap',text)
    def test_two_readonly_pings(self):
        text=(ROOT/'scripts/ai-health-pings.ps1').read_text(encoding='utf-8')
        self.assertIn("classification='HARD'",text)
        self.assertIn("classification='SOFT'",text)
        self.assertIn('127.0.0.1:8713/api/inference/status',text)
        self.assertIn('127.0.0.1:8720/health',text)
        for forbidden in ['Start-ScheduledTask','Stop-ScheduledTask','Start-Service','Stop-Service','Stop-Process']:
            self.assertNotIn(forbidden,text)
if __name__=='__main__':unittest.main()
