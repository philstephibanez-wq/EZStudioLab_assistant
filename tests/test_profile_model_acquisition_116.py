import hashlib
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import (FILE,PINNED_SIZE,PINNED_XET_HASH,PINNED_CONTENT_SHA256,metadata,download)

class OfficialXetIntegrityTests(unittest.TestCase):
 def test_exact_official_hash_pair(self):
  result=metadata(fetch=lambda _: [{"path":FILE,"size":PINNED_SIZE}],integrity=lambda:(PINNED_SIZE,PINNED_XET_HASH))
  self.assertEqual(result["xet_hash"],PINNED_XET_HASH)
  self.assertEqual(result["sha256"],PINNED_CONTENT_SHA256)
  self.assertNotEqual(result["sha256"],result["xet_hash"])
 def test_changed_xet_hash_blocked(self):
  with self.assertRaisesRegex(RuntimeError,"PINNED_XET_HASH_CHANGED"):
   metadata(fetch=lambda _: [{"path":FILE,"size":PINNED_SIZE}],integrity=lambda:(PINNED_SIZE,"b"*64))
 def test_complete_part_verified_without_network(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/"sample.gguf"
   part=target.with_name(target.name+".part")
   payload=b"complete-cached-test-model"
   part.write_bytes(payload)
   info={"size":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),"source":"https://example.invalid"}
   def forbidden(*a,**kw):raise AssertionError("network must never be called")
   download(info,target,opener=forbidden,chunk_size=8)
   self.assertEqual(target.read_bytes(),payload)
   self.assertFalse(part.exists())
if __name__=="__main__":unittest.main()
