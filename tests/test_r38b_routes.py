"""R38b inventory does not modify LAB and handles missing root."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"scripts"/"r38b-discover-catalogue-routes.py"
spec=importlib.util.spec_from_file_location("r38b_routes",p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class R38b(unittest.TestCase):
    def test_missing_console(self):
        with tempfile.TemporaryDirectory() as td:
            result=module.routes_for_lab(td)
            self.assertEqual(result["status"],"lab_console_missing")
            self.assertEqual(result["route_candidates"],[])

    def test_no_mutation_of_path(self):
        with tempfile.TemporaryDirectory() as td:
            before=list(Path(td).iterdir())
            module.routes_for_lab(td)
            self.assertEqual(before,list(Path(td).iterdir()))

if __name__ == "__main__":
    unittest.main()
