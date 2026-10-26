import unittest
from runtime.open_web_sets import analyze, query_for, public_https, search_web, SearchResponseError

P={'job_id':181,'run_id':143,'song_id':42,
   'recording':{'title':'Inch Allah - Salvatore Adamo','artist':'Salvatore Adamo','version':None,'track_id':'42'},
   'assertions':[{'id':'tempo','characteristic':'tempo','value':112.347},
                 {'id':'mesure','characteristic':'mesure','value':'4/4'}]}
class OpenWebSetsContract(unittest.TestCase):
    def test_search_fallback_and_explicit_failure(self):
        calls=[]
        def get(url):
            calls.append(url)
            return '<a href="https://example.org/proof">External article</a>' if 'bing.com' in url else '<html>no results</html>'
        self.assertEqual(search_web('song',get=get)[0]['url'],'https://example.org/proof')
        self.assertEqual(len(calls),2)
        with self.assertRaises(SearchResponseError):
            search_web('song',get=lambda url:'<html>no results</html>')
    def test_engine_redirects_and_public_links(self):
        from runtime.open_web_sets import _search_links
        duck='<a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Frecord">Song</a>'
        google='<a href="/url?q=https%3A%2F%2Fexample.org%2Fmusic&sa=U">Music</a>'
        mojeek='<a href="https://example.org/report">Report</a>'
        self.assertEqual(_search_links(duck,'https://lite.duckduckgo.com/lite/',10)[0]['url'],'https://example.org/record')
        self.assertEqual(_search_links(google,'https://www.google.com/search',10)[0]['url'],'https://example.org/music')
        self.assertEqual(_search_links(mojeek,'https://www.mojeek.com/search',10)[0]['url'],'https://example.org/report')
        self.assertEqual(_search_links('<a href="https://notbing.com/test">ok</a>','https://www.bing.com/search',10)[0]['url'],'https://notbing.com/test')
    def test_multi_engine_fallback_after_empty_html(self):
        calls=[]
        def mock_get(url):
            calls.append(url)
            return '<a href="https://example.org/a">A</a>' if 'mojeek.com' in url else '<html>blocked</html>'
        result=search_web('song',get=mock_get)
        self.assertEqual(result[0]['url'],'https://example.org/a')
        self.assertEqual(len(calls),4)

    def test_filename_identity_query_is_normalized(self):
        self.assertIn('"Inch Allah" "Salvatore Adamo"',query_for(P['recording']))
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
