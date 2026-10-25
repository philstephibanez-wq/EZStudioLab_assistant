import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_final_verifier import final_assertions, verify_final_values
class DynamicApiContract(unittest.TestCase):
    def test_unrestricted_instruments_and_other_dimensions(self):
        data=[{"id":"instruments:"+str(i),"dimension":"instruments","value":v} for i,v in enumerate(["oud","sitar","bassoon","erhu"])]
        data.append({"id":"texture_granular","dimension":"texture","value":"dense"})
        row={"_public_final_assertions":data,"metrics":{"tempo":{"bpm":300}}}
        found=final_assertions(row)
        self.assertEqual(len(found),5)
        self.assertEqual(found[0]["key"],"instrument:0")
        self.assertEqual(found[-1]["value"],"dense")
        verified=verify_final_values(row,{"title":"Example","artist":"Performer"},{"sources":[]})
        self.assertEqual(len(verified["assertions"]),5)
        self.assertTrue(all(x["verdict"]=="non_trouve" for x in verified["assertions"]))
    def test_bad_or_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            final_assertions({"_public_final_assertions":[{"id":"x","dimension":"x","value":"a"},{"id":"x","dimension":"x","value":"b"}]})
if __name__=="__main__":
    unittest.main()
