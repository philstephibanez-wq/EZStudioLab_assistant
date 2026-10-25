import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_resource_sets import exploratory_pass,consolidate
class SetExplorationTest(unittest.TestCase):
    def test_scan_all_items_on_every_page(self):
        texts={"https://a.test":"guitar guitar violin folk","https://b.test":"violin folk"}
        items=[{"id":"instrument:0","value":"guitar"},{"id":"instrument:1","value":"violin"},{"id":"genre","value":"folk"}]
        result=exploratory_pass("song",items,
            lambda query,max_results:[{"url":url} for url in texts],
            lambda url:{"status":"read","url":url,"text":texts[url]})
        counts={tuple(entry["fact"]):entry for entry in result["sets"]["frequencies"]}
        self.assertEqual(counts[("instrument:0","guitar")]["occurrences"],2)
        self.assertEqual(counts[("instrument:0","guitar")]["documents"],1)
        self.assertEqual(counts[("instrument:1","violin")]["documents"],2)
        self.assertEqual(len(result["sets"]["intersections"]),1)
        self.assertFalse(result["sets"]["scientific_verdicts"])
    def test_empty_intersection_preserves_union(self):
        result=consolidate([{"url":"a","occurrences":[{"item_id":"a","value":"piano"}]},
                            {"url":"b","occurrences":[{"item_id":"b","value":"oud"}]}])
        self.assertEqual(result["intersections"],[])
        self.assertEqual(len(result["union"]),2)
    def test_duplicate_resource_rejected(self):
        with self.assertRaises(ValueError):
            consolidate([{"url":"a"},{"url":"a"}])
if __name__=="__main__":unittest.main()
