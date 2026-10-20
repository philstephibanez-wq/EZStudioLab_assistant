from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from declarative_review import load_review_preset, PHASES
from ai_provider import _local_profile_budget

MAIN_PRESET = r'\\EZSTUDIO-MAIN\EZStudio_lab\presets\assistant\profile-baseline-1.json'


def baseline():
    return {
        'schema': 'ezs.assistant.review-preset.v1',
        'id': 'profile-qwen-baseline-1',
        'phase': 'profile',
        'provider': 'local',
        'prompt': 'Review the profile against independent evidence. ' * 8,
        'temperature': 0.1,
        'max_tokens': 3072,
        'context_max_chars': 6500,
    }


def encoded(data):
    return json.dumps(data, ensure_ascii=False).encode('utf-8')


class DeclarativeContract(unittest.TestCase):
    def test_common_phase_registry(self):
        self.assertEqual(PHASES, ('profile', 'stems', 'chords_n', 'lyrics'))

    def test_baseline(self):
        with patch('pathlib.Path.read_bytes', return_value=encoded(baseline())):
            preset, digest = load_review_preset(path=MAIN_PRESET)
        self.assertEqual(preset['temperature'], 0.1)
        self.assertEqual(preset['max_tokens'], 3072)
        self.assertEqual(len(digest), 64)

    def test_repository_preset_matches_budget_contract(self):
        path = ROOT / 'presets' / 'assistant' / 'profile-baseline-1.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(data['max_tokens'], baseline()['max_tokens'])
        self.assertEqual(data['context_max_chars'], baseline()['context_max_chars'])
        self.assertEqual(data['temperature'], baseline()['temperature'])
        self.assertEqual(data['schema'], baseline()['schema'])
        self.assertEqual(data['phase'], 'profile')

    def test_reduced_context_preserves_recording_scoped_evidence(self):
        evidence = {
            'identity': {'title': 'Example', 'artist': 'Example'},
            'profile_view': {'genre': {'predictions': ['rock'] * 300}},
            'public_research': {
                'recording_genres': [{
                    'source': 'MusicBrainz', 'scope': 'recording',
                    'source_url': 'https://musicbrainz.org/recording/example',
                    'genre': 'rock'
                }],
                'recording_credits': [{
                    'musician': 'Example', 'role': 'instrument',
                    'instruments': ['guitar'], 'scope': 'recording',
                    'source_url': 'https://musicbrainz.org/recording/example'
                }],
            },
        }
        reduced = json.loads(_local_profile_budget(evidence, 'system' * 200,
                                                   max_chars=2300))
        self.assertTrue(reduced['context_reduction']['active'])
        public = reduced['public_research']
        self.assertEqual(public['recording_genres'][0]['genre'], 'rock')
        self.assertEqual(public['recording_credits'][0]['instruments'], ['guitar'])
        self.assertEqual(public['recording_credits'][0]['source_url'],
                         'https://musicbrainz.org/recording/example')

    def test_missing_path_fails_closed(self):
        with patch.dict('os.environ', {'EZSTUDIOLAB_REVIEW_PRESET_PATH': ''}):
            with self.assertRaisesRegex(ValueError, 'review_main_preset_path_required'):
                load_review_preset()

    @unittest.skipUnless(sys.platform == 'win32', 'UNC enforcement is Windows-specific')
    def test_local_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'review_preset_requires_main_unc_path'):
            load_review_preset(path=r'H:\EZStudio_lab\presets\assistant\profile-baseline-1.json')

    def test_hot_reload_without_import_reload(self):
        first_data = baseline()
        second_data = {**first_data, 'temperature': 0.35}
        with patch('pathlib.Path.read_bytes', side_effect=[encoded(first_data), encoded(second_data)]):
            first, a = load_review_preset(path=MAIN_PRESET)
            second, b = load_review_preset(path=MAIN_PRESET)
        self.assertEqual(first['temperature'], 0.1)
        self.assertEqual(second['temperature'], 0.35)
        self.assertNotEqual(a, b)

    def test_no_arbitrary_code_or_bad_phase(self):
        invalid = {**baseline(), 'python_module': 'os.system'}
        with patch('pathlib.Path.read_bytes', return_value=encoded(invalid)):
            with self.assertRaisesRegex(ValueError, 'invalid_keys'):
                load_review_preset(path=MAIN_PRESET)
        with self.assertRaisesRegex(ValueError, 'phase_unknown'):
            load_review_preset(phase='untrusted', path=MAIN_PRESET)

    def test_bom_and_invalid_do_not_fallback(self):
        with patch('pathlib.Path.read_bytes', return_value=b'\xef\xbb\xbf' + encoded(baseline())):
            with self.assertRaisesRegex(ValueError, 'bom_forbidden'):
                load_review_preset(path=MAIN_PRESET)
        with patch('pathlib.Path.read_bytes', return_value=b'{broken'):
            with self.assertRaises(json.JSONDecodeError):
                load_review_preset(path=MAIN_PRESET)


if __name__ == '__main__':
    unittest.main()
