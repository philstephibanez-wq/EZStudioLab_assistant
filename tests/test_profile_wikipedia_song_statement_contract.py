"""Wikipédia : seules les citations chanson/genre explicites et exactes sont admissibles."""
import ast
from pathlib import Path
import re
import unittest

P=Path(__file__).resolve().parents[1] / 'app' / 'ai_provider.py'
root=ast.parse(P.read_text(encoding='utf-8'))
functions=[n for n in root.body if isinstance(n, ast.FunctionDef)
           and n.name in ('_verified_wikipedia_song_genre','_verified_dimension_evidence','_profile_ai_coverage')]
ns={'re':re}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(P),'exec'),ns)
URL='https://en.wikipedia.org/wiki/Example_song'
QUOTE='Aline is a pop song by Christophe.'
PAGE={'source':'Wikipedia','scope':'identity_matched_page','source_url':URL,'extract':QUOTE}
CLAIM={'source':'Wikipedia','scope':'song_statement','source_url':URL,'genre':'pop','quote':QUOTE}
IDENTITY={'title':'Aline','artist':'Christophe'}
def count(claim, page=PAGE, identity=IDENTITY):
    raw={'genre':{'decision':'match','confidence':.7,'evidence':[claim]}}
    result=ns['_verified_dimension_evidence'](raw,{'identity':identity,'public_research':{'wikipedia_quotes':[page]}})
    return ns['_profile_ai_coverage'](result)['scored_count']

class SongStatementContract(unittest.TestCase):
    def test_exact_song_genre_quote(self):
        self.assertEqual(count(CLAIM),1)
    def test_artist_biography_does_not_count(self):
        q='Christophe is a pop singer. Aline was a hit.'
        self.assertEqual(count({**CLAIM,'quote':q},{**PAGE,'extract':q}),0)
    def test_wrong_artist_does_not_count(self):
        self.assertEqual(count(CLAIM,identity={'title':'Aline','artist':'Other artist'}),0)
    def test_hallucinated_quote_does_not_count(self):
        self.assertEqual(count({**CLAIM,'quote':'Aline is a rock song by Christophe.'}),0)
    def test_genre_mismatch_does_not_count(self):
        self.assertEqual(count({**CLAIM,'genre':'rock'}),0)
    def test_wrong_page_does_not_count(self):
        self.assertEqual(count(CLAIM,page={**PAGE,'source_url':'https://en.wikipedia.org/wiki/Elsewhere'}),0)
    def test_clap_cannot_count(self):
        self.assertEqual(count({'module':'semantic.clap-open-vocabulary','label':'pop','score':.8}),0)
    def test_generic_instrumentation_wikipedia_cannot_count(self):
        raw={'instrumentation':{'decision':'match','confidence':.8,'evidence':[CLAIM]}}
        result=ns['_verified_dimension_evidence'](raw,{'identity':IDENTITY,'public_research':{'wikipedia_quotes':[PAGE]}})
        self.assertEqual(ns['_profile_ai_coverage'](result)['scored_count'],0)

if __name__=='__main__':
    unittest.main()
