import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import metadata,FILE,PINNED_SIZE,PINNED_XET_HASH,PINNED_CONTENT_SHA256
class MetadataReturnRegression(unittest.TestCase):
 def test_official_file_returns_dict_not_none(self):
  actual=metadata(lambda _: [{"path":FILE,"size":PINNED_SIZE}],lambda:(PINNED_SIZE,PINNED_XET_HASH))
  self.assertIsInstance(actual,dict)
  self.assertEqual(actual["sha256"],PINNED_CONTENT_SHA256)
 def test_fixture_returns_dict(self):
  actual=metadata(lambda _: [{"path":FILE,"size":1100000000,"lfs":{"sha256":"a"*64}}])
  self.assertEqual(actual["sha256"],"a"*64)
 def test_changed_official_xet_is_rejected(self):
  with self.assertRaisesRegex(RuntimeError,"PINNED_XET_HASH_CHANGED"):
   metadata(lambda _: [{"path":FILE,"size":PINNED_SIZE}],lambda:(PINNED_SIZE,"b"*64))
if __name__=="__main__":unittest.main()
