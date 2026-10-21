"""Executable fail-closed contracts for crosscheck source attestations."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_crosscheck import crosscheck, digest


def fixtures(*, redacted=True, attestation=True):
    key="semantic.clap-open-vocabulary"
    original={"id":key,"status":"ok","raw":{"api_key":"private"}}
    archived={"id":key,"status":"ok","raw":{"api_key":"[REDACTED_SECRET_OR_BINARY]" if redacted else "private"}}
    sha=digest(original)
    lab={"schema":"ezstudio.diagnostics.main.v1","producer":"lab","phase":"profile","run_id":153,
         "fields":{"id":153,"item":"profile","diagnostics_json":{"module_registry":{"modules":[archived]}}},
         "redactions":[]}
    if attestation:
        lab["module_integrity"]=[{"module":key,"source_sha256_before_redaction":sha,
                                   "archive_sha256_after_redaction":digest(archived),
                                   "archive_changed":digest(original)!=digest(archived)}]
    review={"schema":"ezstudio.diagnostics.main.v1","producer":"assistant","run_id":153,"revision_id":52,
            "fields":{"id":52,"run_id":153,"comparison_json":{"module_consultations":{
                "complete":True,"examined":1,"item_total":1,"results":[{
                    "item_id":key,"index":1,"source_sha256":sha,"status":"completed",
                    "assessment":{"status":"completed","supporting_evidence":[],
                                  "conflicting_evidence":[],"uncertainty":"not validated"}}]},
                "assistant_ai":{"coverage":{"scored_count":0,"total_count":1}}}}}
    xps={"schema":"ezstudio.profile-execution-report.v1","run_id":153,"revision_id":52,
         "module_audit":{"records":[{"item_id":key,"index":1,"source_sha256":sha,
                                     "status":"completed"}]}}
    return lab,review,xps


class SourceAttestationContracts(unittest.TestCase):
    def test_identical_archive_verifies(self):
        result=crosscheck(*fixtures(redacted=False))
        self.assertTrue(result["integrity_complete"])
        self.assertTrue(result["provenance_checks"][0]["source_hash_verified"])

    def test_redacted_archive_stays_unverified(self):
        result=crosscheck(*fixtures())
        self.assertFalse(result["integrity_complete"])
        self.assertFalse(result["provenance_checks"][0]["source_hash_verified"])
        self.assertTrue(result["provenance_checks"][0]["source_attestation_matches_qwen"])

    def test_legacy_archive_no_attestation_blocks(self):
        result=crosscheck(*fixtures(attestation=False))
        self.assertFalse(result["integrity_complete"])
        self.assertEqual(result["blocking_source_mismatches"],["semantic.clap-open-vocabulary"])

    def test_tampered_post_redaction_sha_rejected(self):
        lab,review,xps=fixtures()
        lab["module_integrity"][0]["archive_sha256_after_redaction"]="0"*64
        with self.assertRaisesRegex(ValueError,"crosscheck_archive_attestation_invalid"):
            crosscheck(lab,review,xps)

    def test_forged_pre_redaction_sha_blocks(self):
        lab,review,xps=fixtures()
        lab["module_integrity"][0]["source_sha256_before_redaction"]="0"*64
        result=crosscheck(lab,review,xps)
        self.assertFalse(result["integrity_complete"])
        self.assertEqual(result["blocking_source_mismatches"],["semantic.clap-open-vocabulary"])

    def test_partial_attestation_rejected(self):
        lab,review,xps=fixtures()
        lab["module_integrity"]=[]
        result=crosscheck(lab,review,xps)
        self.assertFalse(result["integrity_complete"])


if __name__=="__main__":
    unittest.main()
