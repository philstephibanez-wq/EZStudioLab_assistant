import unittest
from runtime.open_web_sets import analyze, query_for, public_https

P={'job_id':181,'run_id':143,'song_id':42,
   'recording':{'title':'Inch Allah - Salvatore Adamo','artist':'Salvatore Adamo','version':None,'track_id':'42'},
   'assertions':[{'id':'tempo','characteristic':'tempo','value':112.347},
                 {'id':'mesure','characteristic':'mesure','value':'4/4'}]}
class OpenWebSetsContract(unittest.TestCase):
    def test_dynamic_queries(self):
        self.assertIn('mesure',query_for(P['recording'],P['assertions'][1]))
    def test_real_set_intersection_from_page_contents(self):
        result=analyze(P,search=lambda q:[{'url':'https://example.org/article','label':'page'}],
                       fetch=lambda url:'<html><body>Inch Allah Salvatore Adamo tempo et mesure</body></html>')
        self.assertEqual(result['read_count'],1)
        self.assertEqual(result['sets']['tempo'],['https://example.org/article'])
        self.assertEqual(len(result['intersections']),1)
        self.assertFalse(result['pages'][0]['evidence_verified'])
        self.assertEqual(result['verdicts'],[])
    def test_unavailable_search_never_invents_a_verdict(self):
        def fail(query):raise OSError('unavailable')
        result=analyze(P,search=fail)
        self.assertEqual(result['read_count'],0)
        self.assertEqual(result['verdicts'],[])
        self.assertTrue(result['errors'])
    def test_public_https(self):
        for url in ['http://example.org','https://127.0.0.1','https://192.168.1.1','https://localhost']:
            self.assertFalse(public_https(url))
    def test_no_scientific_provenance_passes_through(self):
        payload={**P,'diagnostics':{'clap':{'score':0.9}}}
        result=analyze(payload,search=lambda q:[])
        self.assertNotIn('diagnostics',result)
        self.assertNotIn('clap',str(result))
if __name__=='__main__':unittest.main()
