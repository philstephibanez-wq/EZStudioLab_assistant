"""Recording-level vocal categories must be explicit, not inferred from generic vocals."""
import ast
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'app'/'ai_provider.py'
root=ast.parse(P.read_text(encoding='utf-8'))
funcs=[n for n in root.body if isinstance(n,ast.FunctionDef) and n.name in ('_verified_dimension_evidence','_profile_ai_coverage')]
ns={}
exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),str(P),'exec'),ns)
URL='https://musicbrainz.org/recording/example'
def score(dimension, role, attributes, claim_role=None):
    credit={'source_url':URL,'scope':'recording','role':role,'instruments':attributes}
    claim={'source':'MusicBrainz','scope':'recording','source_url':URL,'role':claim_role or role}
    dims={dimension:{'decision':'match','confidence':.8,'evidence':[claim]}}
    verified=ns['_verified_dimension_evidence'](dims,{'public_research':{'recording_credits':[credit]}})
    return ns['_profile_ai_coverage'](verified)['scored_count']
class VocalScopeContract(unittest.TestCase):
    def test_explicit_lead(self):
        self.assertEqual(score('lead_vocal','vocal',['lead vocals']),1)
    def test_generic_vocal_is_not_lead(self):
        self.assertEqual(score('lead_vocal','vocal',['vocal']),0)
    def test_backing_in_relation_attributes(self):
        self.assertEqual(score('backing_vocals','vocal',['backing vocals']),1)
    def test_generic_vocal_is_not_backing(self):
        self.assertEqual(score('backing_vocals','vocal',['vocal']),0)
    def test_explicit_choir(self):
        self.assertEqual(score('choir','vocal',['choir']),1)
    def test_generic_vocal_is_not_choir(self):
        self.assertEqual(score('choir','vocal',['vocal']),0)
    def test_role_mismatch(self):
        self.assertEqual(score('backing_vocals','vocal',['backing vocals'],'producer'),0)
if __name__=='__main__':
    unittest.main()
