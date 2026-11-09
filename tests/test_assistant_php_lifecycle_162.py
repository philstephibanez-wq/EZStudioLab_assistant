import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class AssistantPhpLifecycle162(unittest.TestCase):
    def test_php_command_replaces_vbs(self):
        cmd = (ROOT / 'src/Command/AssistantLlamaEventCommand.php').read_text(encoding='utf-8')
        service = (ROOT / 'src/Service/AssistantLlamaLifecycle.php').read_text(encoding='utf-8')
        self.assertIn('assistant:llama:event', cmd)
        self.assertIn('EZS_FrankenPHP', service)
        self.assertIn('Vulkan1', service)
        self.assertIn('WScript.Shell', service)
        self.assertIn('FRANKENPHP_STOP_LLAMA_TERMINATED_COUNT', service)
        self.assertNotIn('Start-ScheduledTask', service)
    def test_symfony_console_exists_and_is_declared(self):
        import json
        self.assertTrue((ROOT/'bin/console').exists())
        manifest=json.loads((ROOT/'composer.json').read_text(encoding='utf-8'))
        self.assertIn('symfony/console', manifest['require'])
    def test_readonly_probes(self):
        p = (ROOT/'scripts/ai-health-pings.ps1').read_text(encoding='utf-8')
        for marker in ("classification='HARD'", "classification='SOFT'", 'llama_native_count'):
            self.assertIn(marker,p)
        for token in ('Stop-Process','Start-ScheduledTask','Start-Service','Stop-Service'):
            self.assertNotIn(token,p)
    def test_no_periodic_or_vbs(self):
        cmd = (ROOT/'src/Command/AssistantLlamaEventCommand.php').read_text(encoding='utf-8')
        self.assertIn('assistant:llama:event',cmd)
        self.assertNotIn('Start-ScheduledTask',cmd)
        self.assertNotIn('powershell.exe',cmd)
        self.assertNotIn('wscript.exe',cmd)

if __name__=='__main__':unittest.main()
