import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import metadata,FILE
class XetIntegrityTest(unittest.TestCase):
 def test_xet_fallback(self):
  result=metadata(lambda _: [{"path":FILE,"size":1110000000}],integrity=lambda:(1110000000,"a"*64))
  self.assertEqual(result["sha256"],"a"*64)
 def test_xet_size_mismatch_rejected(self):
  with self.assertRaisesRegex(RuntimeError,"UPSTREAM_SIZE_MISMATCH"):
   metadata(lambda _: [{"path":FILE,"size":1110000000}],integrity=lambda:(1110000001,"a"*64))
 def test_bad_xet_hash_rejected(self):
  with self.assertRaisesRegex(RuntimeError,"UPSTREAM_SIZE_OR_SHA256_UNAVAILABLE"):
   metadata(lambda _: [{"path":FILE,"size":1110000000}],integrity=lambda:(1110000000,"not-a-sha"))
if __name__=="__main__":unittest.main()
