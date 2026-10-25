"""Generic coverage contract: every emitted musician-facing instrument is an assertion."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_final_verifier import final_assertions

class DynamicInstrumentCoverage(unittest.TestCase):
    def test_arbitrary_instrument_lists(self):
        for names in ([], ["oud"], ["bassoon", "sitar", "accordion", "erhu"]):
            with self.subTest(names=names):
                row={"diagnostics":{"profile_view":{"instrumentation":{"candidates":[{"label":n} for n in names]}}}}
                got=[x["value"] for x in final_assertions(row) if x["key"].startswith("instrument:")]
                self.assertEqual(got,names)
    def test_no_scientific_internal_data_escapes(self):
        row={"diagnostics":{"profile_view":{"instrumentation":{"candidates":[{"label":"oud"}]},"modules":[{"id":"PRIVATE_MODULE","scores":[0.99]}]}},"preset":"PRIVATE_PRESET"}
        self.assertNotIn("PRIVATE",str(final_assertions(row)))
if __name__=="__main__":
    unittest.main()
