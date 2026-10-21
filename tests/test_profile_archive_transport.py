import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from download_profile_archive_verified import validate_archive,digest

class ArchiveTransportTest(unittest.TestCase):
    def fixture(self):
        module={"id":"semantic.clap-open-vocabulary","normalized":{"genre":"chanson française"}}
        sha=digest(module)
        return {"schema":"ezstudio.diagnostics.main.v1","producer":"lab",
                "phase":"profile","run_id":153,
                "fields":{"id":153,"diagnostics_json":{"module_registry":{"modules":[module]}}},
                "module_integrity":[{"module":module["id"],"source_sha256_before_redaction":sha,
                                      "archive_sha256_after_redaction":sha,"archive_changed":False}]}

    def test_valid_utf8(self):
        value=json.dumps(self.fixture(),ensure_ascii=False).encode("utf-8")
        self.assertEqual(validate_archive(value,153),1)

    def test_modified_unicode_rejected(self):
        value=self.fixture()
        value["fields"]["diagnostics_json"]["module_registry"]["modules"][0]["normalized"]["genre"]="chanson francaise"
        with self.assertRaisesRegex(ValueError,"archive_sha_mismatch"):
            validate_archive(json.dumps(value).encode("utf-8"),153)

    def test_wrong_run_rejected(self):
        with self.assertRaisesRegex(ValueError,"unexpected_lab_archive_identity"):
            validate_archive(json.dumps(self.fixture()).encode("utf-8"),152)

if __name__=="__main__":
    unittest.main()
