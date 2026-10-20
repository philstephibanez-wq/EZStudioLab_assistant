"""Wikipedia remains bounded context, never a self-validating model citation."""
import ast
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[1]/'app'/'ai_provider.py'
src=P.read_text(encoding='utf-8')
tree=ast.parse(src)
fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_verified_dimension_evidence','_profile_ai_coverage')]
ns={}
exec(compile(ast.fix_missing_locations(ast.Module(body=fns,type_ignores=[])),str(P),'exec'),ns)

class WikipediaContextContract(unittest.TestCase):
    def test_wikipedia_claim_is_not_verified_musical_fact(self):
        quoted={'source':'Wikipedia','source_url':'https://en.wikipedia.org/wiki/Aline_(song)',
                'scope':'identity_matched_page','quote':'A pop song'}
        value={'genre':{'decision':'match','confidence':.95,'evidence':[quoted]}}
        v=ns['_verified_dimension_evidence'](value,{'public_research':{
            'wikipedia_quotes':[{'source':'Wikipedia','source_url':quoted['source_url'],
                                 'scope':'identity_matched_page','extract':'A pop song'}]}})
        self.assertEqual(ns['_profile_ai_coverage'](v)['scored_count'],0)
        self.assertEqual(v['genre']['reason'],'no_verified_external_dimension_evidence')

    def test_unrelated_page_is_not_scored(self):
        claim={'source':'Wikipedia','source_url':'https://en.wikipedia.org/wiki/Unrelated',
               'scope':'identity_matched_page','quote':'backing vocals'}
        value={'backing_vocals':{'decision':'match','confidence':.98,'evidence':[claim]}}
        result=ns['_verified_dimension_evidence'](value,{'public_research':{'wikipedia_quotes':[]}})
        self.assertEqual(result['backing_vocals']['decision'],'not_scored')

    def test_wikipedia_context_is_bounded_and_only_identity_checked(self):
        code=ast.get_source_segment(src,next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                                              and n.name=='_local_profile_evidence'))
        self.assertIn("source.get('identity_relevant') is True",code)
        self.assertIn("extract[:2500]",code)
        self.assertIn("'wikipedia_quotes': wikipedia_quotes[:2]",code)

if __name__=='__main__':
    unittest.main()
