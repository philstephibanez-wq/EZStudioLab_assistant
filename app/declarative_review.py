"""Declarative Assistant review configuration, deliberately separate from LAB science presets."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

PHASES = ('profile', 'stems', 'chords_n', 'lyrics')
ALLOWED = {'schema', 'id', 'phase', 'provider', 'prompt', 'temperature', 'max_tokens', 'context_max_chars'}
DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'presets' / 'assistant' / 'profile-baseline-1.json'


def load_review_preset(phase='profile', path=None):
    """Read on EACH invocation: changes require no worker restart. Fail closed."""
    if phase not in PHASES:
        raise ValueError('review_phase_unknown')
    selected = Path(path or os.getenv('EZSTUDIOLAB_REVIEW_PRESET_PATH') or DEFAULT_PATH)
    raw = selected.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raise ValueError('review_preset_bom_forbidden')
    if len(raw) > 32768:
        raise ValueError('review_preset_oversized')
    data = json.loads(raw.decode('utf-8', errors='strict'))
    if not isinstance(data, dict) or set(data) != ALLOWED:
        raise ValueError('review_preset_invalid_keys')
    if data['schema'] != 'ezs.assistant.review-preset.v1' or data['phase'] != phase:
        raise ValueError('review_preset_schema_phase_mismatch')
    if not isinstance(data['id'], str) or not 1 <= len(data['id']) <= 90 or not all(c.isalnum() or c in '._-' for c in data['id']):
        raise ValueError('review_preset_invalid_id')
    if data['provider'] != 'local':
        raise ValueError('review_preset_provider_not_supported')
    if not isinstance(data['prompt'], str) or not 100 <= len(data['prompt']) <= 12000:
        raise ValueError('review_preset_invalid_prompt')
    t = data['temperature']
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t <= 1:
        raise ValueError('review_preset_invalid_temperature')
    for field, low, high in [('max_tokens', 200, 4096), ('context_max_chars', 2000, 16000)]:
        n = data[field]
        if isinstance(n, bool) or not isinstance(n, int) or not low <= n <= high:
            raise ValueError('review_preset_invalid_' + field)
    return data, hashlib.sha256(raw).hexdigest()
