"""Do not promote scientific model outputs to independent external evidence."""
import ast
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / 'app' / 'ai_provider.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('_verified_dimension_evidence', '_profile_ai_coverage')]
scope = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(source),'exec'), scope)

URL = 'https://musicbrainz.org/recording/example'
external = {'public_research': {'recording_credits': [{
    'source_url': URL, 'scope': 'recording', 'role': 'guitar',
    'instruments': ['guitar'], 'musician': 'Example'}]}}
def check(name, evidence, sources=external):
    dims = {name: {'decision':'match','confidence':.8,'evidence':evidence}}
    result = scope['_verified_dimension_evidence'](dims,sources)
    return scope['_profile_ai_coverage'](result)

class ProvenanceContract(unittest.TestCase):
    def test_lab_scores_never_count(self):
        result = check('genre',[{'module':'semantic.clap-open-vocabulary','label':'folk','score':.8}])
        self.assertEqual(result['scored_count'],0)
        self.assertEqual(result['dimensions']['genre']['reason'],'no_verified_external_dimension_evidence')

    def test_fabricated_external_url_never_counts(self):
        result = check('instrumentation',[{'source':'MusicBrainz','scope':'recording',
            'source_url':'https://musicbrainz.org/recording/unknown','instrument':'guitar'}])
        self.assertEqual(result['scored_count'],0)

    def test_verified_recording_instrument_can_count(self):
        result = check('instrumentation',[{'source':'MusicBrainz','scope':'recording',
            'source_url':URL,'instrument':'guitar'}])
        self.assertEqual(result['scored_count'],1)

    def test_album_or_genre_tag_is_not_recording_credit(self):
        result = check('genre',[{'source':'MusicBrainz','scope':'recording',
            'source_url':URL,'instrument':'guitar'}])
        self.assertEqual(result['scored_count'],0)

    def test_no_credits_no_score(self):
        result = check('instrumentation',[{'source':'MusicBrainz','scope':'recording',
            'source_url':URL,'instrument':'guitar'}],{'public_research': {'sources':[]}})
        self.assertEqual(result['scored_count'],0)

if __name__ == '__main__':
    unittest.main()
