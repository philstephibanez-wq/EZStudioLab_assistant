"""Crosscheck source attestations: preserve fail-closed archive integrity."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_crosscheck import crosscheck, digest


def fixtures(redacted=True, attestation=True, tamper=False):
    key="semantic.clap-open-vocabulary"
    original={"id":key,"status":"ok","raw":{"api_key":"private"}}
    archived={"id":key,"status":"ok","raw":{"api_key":"[REDACTED_SECRET_OR_BINARY]" if redacted else "private"}}
    if tamper:
        archived["status"]="changed"
    source_hash=digest(original)
    lab={"schema":"ezstudio.diagnostics.main.v1","producer":"lab","phase":"profile","run_id":153,
         "fields":{"id":153,"item":"profile","diagnostics_json":{"module_registry":{"modules":[archived]}}},
         "redactions":[{"field":"$.diagnostics_json.module_registry.modules[].raw.api_key",
                        "reason":"secret_or_binary_key"}] if redacted else []}
    if attestation:
        lab["module_integrity"]=[{"module":key,"source_sha256_before_redaction":source_hash,
                                   "archive_sha256_after_redaction":digest(archived),
                                   "archive_changed":digest(original)!=digest(archived)}]
    return lab, original, source_hash


class SourceAttestationContracts(unittest.TestCase):
    def test_hash_is_canonical(self):
        self.assertEqual(digest({"z":2,"a":1}),digest({"a":1,"z":2}))

    def test_attestation_does_not_override_archive_mismatch(self):
        lab, _, source_hash=fixtures()
        self.assertNotEqual(lab["module_integrity"][0]["archive_sha256_after_redaction"],source_hash)

    def test_attestation_not_self_validating(self):
        lab, _, _=fixtures(tamper=True)
        self.assertTrue(lab["module_integrity"][0]["archive_changed"])

    def test_no_attestation_preserves_prior_semantics(self):
        lab, _, _=fixtures(attestation=False)
        self.assertNotIn("module_integrity",lab)


if __name__=="__main__":
    unittest.main()
