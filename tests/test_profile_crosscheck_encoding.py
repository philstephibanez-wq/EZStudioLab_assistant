import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from crosscheck_profile_archives import read_json

class EncodingTest(unittest.TestCase):
    def test_utf16_le_bom_from_windows_powershell(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"report.json"
            p.write_bytes('{"run_id":153,"label":"évaluation"}'.encode("utf-16"))
            self.assertEqual(read_json(p)["label"],"évaluation")
    def test_utf8_bom(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"report.json"
            p.write_bytes('{"run_id":153}'.encode("utf-8-sig"))
            self.assertEqual(read_json(p)["run_id"],153)

if __name__=="__main__":unittest.main()
