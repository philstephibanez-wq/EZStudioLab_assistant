import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ProfileReloadContract(unittest.TestCase):
 def test_guarded_reload_discovers_without_executing_launcher(self):
  s=(ROOT/'scripts/reload-profile-guardian.ps1').read_text(encoding='utf-8')
  self.assertIn('Parser]::ParseFile',s)
  self.assertIn('PROFILE_RELOAD_RELAY_CREDENTIALS_UNAVAILABLE_IN_APPROVED_SOURCES',s)
  self.assertIn("Maintenance 'pause'",s)
  self.assertIn('$reloadSucceeded -and',s)
  self.assertNotIn('& $launcher',s)
  self.assertNotIn('Write-Output $token',s)
 def test_version_commit_policy(self):
  s=(ROOT/'AGENTS.md').read_text(encoding='utf-8')
  self.assertIn('Le préfixe `[v]` est interdit',s)
  self.assertIn('[1.5b]',s)
