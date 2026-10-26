import hashlib
import io
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_acquisition import download

class FakeResponse:
 def __init__(self,code,content,header):
  self.code=code
  self.stream=io.BytesIO(content)
  self.headers={"Content-Range":header}
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def getcode(self):return self.code
 def read(self,n):return self.stream.read(n)

class ResumableDownloadTest(unittest.TestCase):
 def setUp(self):
  self.data=b"abcdef"*10
  self.info={"size":len(self.data),"sha256":hashlib.sha256(self.data).hexdigest(),"source":"https://example.test/model"}
 def server(self,req,timeout):
  header=req.get_header("Range")
  self.assertIsNotNone(header)
  start,end=(int(x) for x in header[6:].split("-"))
  return FakeResponse(206,self.data[start:end+1],f"bytes {start}-{end}/{len(self.data)}")
 def test_complete(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/"model.gguf"
   download(self.info,target,opener=self.server,chunk_size=16)
   self.assertEqual(target.read_bytes(),self.data)
   self.assertFalse(target.with_name("model.gguf.part").exists())
 def test_resume(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/"model.gguf"
   target.with_name("model.gguf.part").write_bytes(self.data[:13])
   download(self.info,target,opener=self.server,chunk_size=16)
   self.assertEqual(target.read_bytes(),self.data)
 def test_wrong_http_range_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/"model.gguf"
   with self.assertRaisesRegex(RuntimeError,"UPSTREAM_RANGE_UNSUPPORTED"):
    download(self.info,target,opener=lambda req,timeout:FakeResponse(200,b"bad",""),chunk_size=16)
   self.assertFalse(target.exists())
 def test_bad_hash_not_published(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/"model.gguf"
   info=dict(self.info,sha256="0"*64)
   with self.assertRaisesRegex(RuntimeError,"DOWNLOAD_SHA256_MISMATCH"):
    download(info,target,opener=self.server,chunk_size=16)
   self.assertFalse(target.exists())
   self.assertEqual(target.with_name("model.gguf.part").stat().st_size,len(self.data))
if __name__=="__main__":unittest.main()
