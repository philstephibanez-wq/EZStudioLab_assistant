import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_musical_facts import evaluate_reference

class ReferenceTests(unittest.TestCase):
    def test_explicit_tempo_contradiction(self):
        item={"key":"tempo","value":"123.0 BPM"}
        src={"url":"https://example.com/song","fact_scope":"recording",
             "musical_facts":{"tempo":{"explicit":True,"value":"118 BPM","url":"https://example.com/song"}}}
        self.assertEqual(evaluate_reference(item,src)["verdict"],"faux")

    def test_album_facts_never_validate(self):
        item={"key":"meter","value":"4/4"}
        src={"url":"https://example.com/album","fact_scope":"album",
             "musical_facts":{"meter":{"explicit":True,"value":"4/4","url":"https://example.com/album"}}}
        self.assertIsNone(evaluate_reference(item,src))

    def test_ambiguous_tempo_half_time(self):
        item={"key":"tempo","value":"123.0 BPM"}
        src={"url":"https://example.com/song","fact_scope":"recording",
             "musical_facts":{"tempo":{"explicit":True,"value":"61.5 BPM","url":"https://example.com/song"}}}
        self.assertIsNone(evaluate_reference(item,src))

if __name__=="__main__":
    unittest.main()
