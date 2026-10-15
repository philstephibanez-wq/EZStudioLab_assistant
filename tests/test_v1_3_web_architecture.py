from __future__ import annotations
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AssistantWebArchitectureV13(unittest.TestCase):
  def test_stack_contract(self):
    req=json.loads((ROOT/'composer.json').read_text(encoding='utf-8'))['require']
    for x in ('symfony/framework-bundle','symfony/twig-bundle','symfony/monolog-bundle','symfony/process'): self.assertIn(x,req)
    self.assertNotIn('doctrine/orm',req); self.assertNotIn('doctrine/doctrine-bundle',req)
  def test_no_database(self):
    c=(ROOT/'src/Controller/DashboardController.php').read_text(encoding='utf-8'); s=(ROOT/'app/web_status.py').read_text(encoding='utf-8')
    self.assertIn("'database'=>false",c); self.assertIn('"database":False',s); self.assertIn('"persistence_owner":"LAB"',s)
  def test_network_boundaries(self):
    s=(ROOT/'app/web_status.py').read_text(encoding='utf-8'); self.assertIn('"transport":"REST"',s); self.assertIn('"transport":"SMB"',s); self.assertIn('"scope":"AI models only"',s)
  def test_front(self):
    b=(ROOT/'templates/base.html.twig').read_text(encoding='utf-8'); d=(ROOT/'templates/dashboard/index.html.twig').read_text(encoding='utf-8')
    self.assertIn('jquery-3.7.1.min.js',b); self.assertIn("$.getJSON('/api/status')",d)
  def test_caddy(self):
    c=(ROOT/'Caddyfile').read_text(encoding='utf-8'); self.assertIn(':8712',c); self.assertIn('127.0.0.1:8713',c)
if __name__=='__main__': unittest.main()
