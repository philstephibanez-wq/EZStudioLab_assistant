"""Research collection protects Wikipedia calls and recording metadata provenance."""
import ast
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / 'app' / 'profile_auto_review.py'
tree = ast.parse(SRC.read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'research_public_sources')
budget = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NetworkBudget')
mb = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_musicbrainz')

class ResearchContract(unittest.TestCase):
    def test_wikipedia_has_priority_over_wikidata(self):
        calls = [n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertIn('_wikipedia', calls)
        self.assertIn('_wikidata', calls)
        self.assertLess(calls.index('_wikipedia'), calls.index('_wikidata'))

    def test_budget_has_room_for_all_sources(self):
        vals = [n.value.value for n in budget.body if isinstance(n, ast.AnnAssign)
                and isinstance(n.target, ast.Name) and n.target.id == 'max_requests_per_item']
        self.assertEqual(vals, [10])

    def test_recording_genres_separate_from_enrichment(self):
        text = ast.get_source_segment(SRC.read_text(encoding='utf-8'), mb)
        self.assertLess(text.index('recording_genres = list(genres)'), text.index('# Enrichment: release-group'))
        self.assertIn('"recording_genres": sorted(set(recording_genres))', text)
        self.assertIn('"recording_tags": sorted(set(recording_tags))', text)

if __name__ == '__main__':
    unittest.main()
