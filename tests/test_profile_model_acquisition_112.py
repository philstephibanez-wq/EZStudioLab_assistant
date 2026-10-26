import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import metadata,dest,FILE
class AcquisitionTests(unittest.TestCase):
 def test_sha_required(self):
  with self.assertRaises(RuntimeError):
   metadata(lambda u:[{"path":FILE,"size":1100000000,"lfs":{}}])
 def test_remote_metadata(self):
  expected="a"*64
  result=metadata(lambda u:[{"path":FILE,"size":1100000000,"lfs":{"sha256":expected}}])
  self.assertEqual(result["sha256"],expected)
 def test_no_wrong_model(self):
  with self.assertRaises(RuntimeError):
   metadata(lambda u:[{"path":"unexpected.gguf","size":1100000000,"lfs":{"sha256":"a"*64}}])
if __name__=="__main__":unittest.main()
