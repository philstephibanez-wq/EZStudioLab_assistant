import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_discovery_funnel import discover_source_sets

class DiscoveryFunnelTests(unittest.TestCase):
    def test_short_query_and_dynamic_refinement(self):
        calls=[]
        def search(query,max_results):
            calls.append(query)
            if len(calls)==1:
                return [{"url":"https://one.example/a","title":"Hotel California Eagles live 1977","snippet":"Album credits guitar bass"}]
            return [{"url":"https://two.example/b","title":"Hotel California Eagles recording","snippet":"guitar bass"}]
        def fetch(url):return {"status":"read","url":url,"text":"guitar bass guitar"}
        items=[{"id":"instrument:1","value":"guitar"},{"id":"instrument:2","value":"bass"}]
        result=discover_source_sets({"title":"Hotel California","artist":"The Eagles"},items,search,fetch,rounds=2)
        self.assertEqual(calls[0],"hotel california eagles")
        self.assertIn("live",calls[1])
        self.assertEqual(result["documents_read"],2)
        counts={tuple(x["fact"]):x for x in result["sets"]["frequencies"]}
        self.assertEqual(counts[("instrument:1","guitar")]["occurrences"],4)
        self.assertEqual(counts[("instrument:1","guitar")]["documents"],2)
        self.assertFalse(result["automatic_verdicts"])

    def test_filters_irrelevant_links_without_whitelist(self):
        def search(query,max_results):return [
            {"url":"https://random.example/m","title":"Breakfast in America Supertramp","snippet":"song piano"},
            {"url":"https://sports.example/m","title":"Football and tennis","snippet":"league scores"}]
        result=discover_source_sets({"title":"Breakfast in America","artist":"Supertramp"},
            [{"id":"instrument:1","value":"piano"}],search,
            lambda url:{"status":"read","text":"piano","url":url},rounds=1)
        self.assertEqual(result["documents_read"],1)
        self.assertEqual(len(result["rounds"][0]["rejected"]),1)

    def test_budget_and_no_item_queries(self):
        calls=[]
        def search(query,max_results):
            calls.append(query)
            return [{"url":"https://x.example/"+str(len(calls)),"title":"Hotel California Eagles","snippet":"No other hints"}]
        result=discover_source_sets({"title":"Hotel California","artist":"Eagles"},
            [{"id":"tempo","value":"92 BPM"}],search,
            lambda url:{"status":"read","text":"92 BPM","url":url},rounds=3,max_documents=1)
        self.assertEqual(len(calls),1)
        self.assertEqual(result["documents_read"],1)

    def test_no_title(self):
        result=discover_source_sets({"title":"","artist":"Eagles"},[],lambda *a,**k:[],lambda x:{})
        self.assertEqual(result["status"],"identity_unavailable")
if __name__=="__main__":unittest.main()
