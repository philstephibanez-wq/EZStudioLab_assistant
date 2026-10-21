import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LabParityContract(unittest.TestCase):
 def test_gpu_lab_fields_and_ui(self):
  php=(ROOT/"src/Controller/GpuTelemetryController.php").read_text(encoding="utf-8")
  ui=(ROOT/"templates/_gpu_monitor.html.twig").read_text(encoding="utf-8")
  js=(ROOT/"public/js/ezstudio-assistant-gpu.js").read_text(encoding="utf-8")
  for name in ("utilization.gpu","memory.used","temperature.gpu","power.draw","clocks.sm","pstate"):
   self.assertIn(name,php)
  for name in ("data-perf-line","data-stat-memory","data-perf-area","data-perf-status"):
   self.assertIn(name,ui)
  self.assertIn("120000",js)
  self.assertIn("2000",js)
 def test_dictionary_projection_declares_omissions(self):
  import sys
  sys.path.insert(0,str(ROOT/"app"))
  from profile_module_compact import _project
  projected=_project({"id":"x",**{str(i):i for i in range(150)}},2)
  self.assertEqual(projected["_projection_coverage"]["original_keys"],151)
  self.assertGreater(projected["_projection_coverage"]["omitted_keys"],0)
