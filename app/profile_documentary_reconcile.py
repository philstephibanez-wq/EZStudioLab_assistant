"""Conservative documentary reconciliation: search snippets never verify identities."""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from profile_adaptive_keywords import terms

def _similar(a, b):
    left, right = terms(a), terms(b)
    if not left or not right:
        return False
    if sorted(left) == sorted(right):
        return True
    initial = re.match(r'^\s*([A-Za-z])\.\s*([A-Za-z]+)\s*$', str(a))
    if initial and len(right) == 2:
        surname = initial.group(2).casefold()
        return any(w.startswith(initial.group(1).casefold()) for w in right) and any(
            w[0] == surname[0] and SequenceMatcher(None, surname, w).ratio() >= .78 for w in right)
    if len(left) != len(right):
        return False
    remaining = right[:]
    for token in left:
        choices = [candidate for candidate in remaining if token == candidate or
                   (len(token) == 1 and candidate.startswith(token)) or
                   (len(candidate) == 1 and token.startswith(candidate)) or
                   (len(token) >= 4 and len(candidate) >= 4 and token[0] == candidate[0] and
                    SequenceMatcher(None, token, candidate).ratio() >= .78)]
        if not choices:
            return False
        remaining.remove(max(choices, key=lambda s: SequenceMatcher(None, token, s).ratio()))
    return not remaining

def _artist_from_hit(title, hit_title):
    """Extract possible performer names from bounded search headlines, never verified evidence."""
    headline = str(hit_title or '')[:180]
    title_tokens = set(terms(title))
    chunks = [headline]
    chunks += re.split(r'\s+(?:-|–|—|~|\|)\s+', headline)
    chunks += re.split(r'\s*[:|]\s*', headline)
    candidates = []
    for chunk in chunks:
        chunk = re.sub(r'\s*\([^)]*(?:official|video|audio|lyrics|clip|live)[^)]*\).*$', '', chunk, flags=re.I).strip()
        chunk = re.sub(r'\s*\[[^]]*\]\s*$', '', chunk).strip()
        words = terms(chunk)
        if not words or len(words) > 6 or set(words).intersection(title_tokens):
            continue
        if chunk.casefold() in ('wikipedia', 'youtube', 'genius', 'lyrics', 'official video', 'audio', 'music video'):
            continue
        candidates.append(chunk)
    return list(dict.fromkeys(candidates))[:5]

def reconcile(title, artist_hint, web, recordings):
    evidence = []
    artist_candidates = sorted({a for rec in recordings for a in rec.get('artist_candidates', [])
                                if isinstance(a, str) and a.strip()})
    matched = [a for a in artist_candidates if artist_hint and _similar(artist_hint, a)]
    for hit in web.get('candidates', [])[:8]:
        headline = str(hit.get('title') or '')
        title_tokens = set(terms(title))
        if not title_tokens or len(title_tokens.intersection(terms(headline))) < min(2, len(title_tokens)):
            continue
        extracted = _artist_from_hit(title, headline)
        corroborated = [name for name in extracted if artist_hint and _similar(artist_hint, name)]
        web_mb = [name for name in artist_candidates if any(_similar(name, candidate) for candidate in extracted)]
        evidence.append({'url': hit.get('url'), 'artist_hint_supported': bool(corroborated),
                         'artist_candidates_extracted': extracted,
                         'artist_matches_unverified': corroborated,
                         'musicbrainz_web_artist_overlap': web_mb,
                         'source_kind': 'search_snippet_only'})
    return {'status': 'hypotheses_only', 'work_title_supported_by_snippets': bool(evidence),
            'artist_hint': artist_hint, 'musicbrainz_artist_matches': matched,
            'musicbrainz_other_artists': [a for a in artist_candidates if a not in matched],
            'documentary_links': evidence[:8],
            'work_identity_verified': False, 'performer_identity_verified': False,
            'recording_identity_verified': False}
