"""Only identity-checked recording genres are admissible; no artist/album tags."""
import ast
import re
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'app'/'ai_provider.py'
root=ast.parse(p.read_text(encoding='utf-8'))
functions=[n for n in root.body if isinstance(n,ast.FunctionDef) and n.name in ('_verified_wikipedia_song_genre', '_verified_dimension_evidence', '_profile_ai_coverage')]
scope={'re': re}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(p),'exec'),scope)
url='https://musicbrainz.org/recording/example'
def run(claim, references):
    dims={'genre':{'decision':'match','confidence':.8,'evidence':[claim]}}
    validated=scope['_verified_dimension_evidence'](dims,{'public_research':{'recording_genres':references}})
    return scope['_profile_ai_coverage'](validated)
class RecordingGenreProvenance(unittest.TestCase):
    def test_identical_recording_fact_can_pass(self):
        fact={'source':'MusicBrainz','scope':'recording','source_url':url,'genre':'pop'}
        self.assertEqual(run(fact,[fact])['scored_count'],1)
    def test_artist_genre_is_not_recording_fact(self):
        fact={'source':'MusicBrainz','scope':'artist','source_url':url,'genre':'pop'}
        self.assertEqual(run(fact,[fact])['scored_count'],0)
    def test_hallucinated_genre_cannot_pass(self):
        fact={'source':'MusicBrainz','scope':'recording','source_url':url,'genre':'folk'}
        ref={'source':'MusicBrainz','scope':'recording','source_url':url,'genre':'pop'}
        self.assertEqual(run(fact,[ref])['scored_count'],0)
    def test_wrong_recording_url_cannot_pass(self):
        fact={'source':'MusicBrainz','scope':'recording','source_url':url+'/wrong','genre':'pop'}
        ref={'source':'MusicBrainz','scope':'recording','source_url':url,'genre':'pop'}
        self.assertEqual(run(fact,[ref])['scored_count'],0)
    def test_lab_score_never_passes(self):
        self.assertEqual(run({'module':'semantic.clap-open-vocabulary','label':'pop','score':.8},[])['scored_count'],0)
if __name__=='__main__':
    unittest.main()
