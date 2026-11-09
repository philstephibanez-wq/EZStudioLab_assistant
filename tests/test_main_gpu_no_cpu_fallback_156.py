"""Contrat statique durable : pas de distribution CPU implicite ni de lanceur supprime."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MainGpuNoCpuFallback156(unittest.TestCase):
    def test_gpu_fail_closed(self):
        text = (ROOT / 'scripts' / 'install-main.ps1').read_text(encoding='utf-8')
        self.assertNotIn('win-cpu-x64', text)
        self.assertNotIn('Invoke-WebRequest', text)
        self.assertNotIn('Expand-Archive', text)
        self.assertIn('GPU_LLAMA_RUNTIME_MISSING_NO_CPU_FALLBACK', text)
        self.assertIn('GPU_LLAMA_VULKAN1_RTX2060_NOT_VERIFIED_NO_CPU_FALLBACK', text)
        self.assertIn('Get-SmbShare -Name EZModels', text)
        self.assertIn('New-Item -ItemType Junction', text)
        self.assertIn('PROFILE_LAUNCHER=', text)
        self.assertIn('PORT_OCCUPIED:', text)

    def test_no_caddy_dependency(self):
        text = (ROOT / 'scripts' / 'install-main.ps1').read_text(encoding='utf-8')
        self.assertNotIn('H:\\Caddy', text)
        self.assertNotIn('SHARED_CADDY_MISSING', text)
        self.assertNotIn('caddy.exe', text.lower())

    def test_legacy_start_fails_closed(self):
        text = (ROOT / 'scripts' / 'install-main.ps1').read_text(encoding='utf-8')
        self.assertIn('if($Start){throw', text)
        self.assertNotIn('& (Join-Path $root', text)
        self.assertIn('MAIN_PREFLIGHT_READ_ONLY_OK', text)
        self.assertIn('MAIN_INSTALL_READY', text)

if __name__ == '__main__':
    unittest.main()
