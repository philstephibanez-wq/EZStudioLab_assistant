import sys
import unittest
from pathlib import Path, PureWindowsPath
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import dest,ROOT,FILE
class WindowsShareTests(unittest.TestCase):
 def test_share_root_has_empty_name_on_windows(self):
  self.assertEqual(PureWindowsPath(ROOT).name,"")
 def test_target_under_expected_share(self):
  target=PureWindowsPath(str(dest(ROOT)))
  self.assertEqual(str(target),str(PureWindowsPath(ROOT)/"assistant"/"bench"/"qwen3-1.7b-q4_k_m"/FILE))
 def test_reject_other_shares(self):
  for root in (r"\\other-server\EZModels",r"\\EZSTUDIO-MAIN\OtherShare",r"C:\EZModels",r"\\EZSTUDIO-MAIN\EZModels\elsewhere"):
   with self.assertRaises(ValueError):dest(root)
if __name__=="__main__":unittest.main()
