"""LAB-triggered PROFILE review. XPS only, no model files written to MAIN."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
import traceback
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(r'C:\EZStudioLab_assistant')
sys.path.insert(0, str(ROOT/'app'))
import main as assistant_main
from profile_review import normalize_track_identity
from profile_auto_review import (
    NetworkBudget, research_public_sources, build_review_payload,
    _run_ai_profile_review, enrich_review_payload_with_ai,
    enrich_review_payload_with_documentary,
)
from ai_provider import build_ai_provider_from_env
from profile_trace import Trace, activate, enabled, emit, snap, purge
from profile_report import publish_trace
from profile_lab_observations import attach_lab_observations
from profile_identity import resolve_missing_artist
from profile_sequential_review import examine_modules
from profile_module_qwen import infer_module
from profile_final_verifier import verify_final_values
from profile_recording_disambiguation import duration_from_catalog
from profile_web_investigator import research_each_assertion
from profile_web_local_review import review_web_items

BASE = os.environ.get('EZSTUDIOLAB_ASSISTANT_BASE_URL', 'http://EZSTUDIO-MAIN:8702').rstrip('/')
TOKEN = os.environ.get('EZSTUDIOLAB_ASSISTANT_TOKEN', '')
PATH = '/internal/analysis/desktop/profile/ai-requests'

def api(path, data=None):
    if not TOKEN:
        raise RuntimeError('token_missing')
    headers = {'X-EZScore-Analysis-Token': TOKEN, 'Accept': 'application/json'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(
        BASE + path,
        data=None if data is None else json.dumps(data).encode('utf-8'),
        headers=headers,
        method='GET' if data is None else 'POST',
    )
    begin = time.perf_counter_ns()
    emit('lab.http.request', {'method': req.get_method(), 'url': BASE + path, 'body': data, 'headers': headers})
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            raw = res.read()
            emit('lab.http.response', {'status': res.status, 'headers': dict(res.headers), 'raw_body': raw.decode('utf-8', 'replace')}, start_ns=begin)
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', 'replace')
        emit('lab.http.error', {'status': exc.code, 'body': detail, 'url': BASE + path}, start_ns=begin)
        raise
    except Exception as exc:
        emit('lab.http.error', {'type': type(exc).__name__, 'message': str(exc), 'url': BASE + path}, start_ns=begin)
        raise

def require_completed_ai_review(ai):
    """Accept evidence-based abstentions as draft; reject invalid or failed inferences."""
    if not isinstance(ai, dict) or ai.get('status') != 'completed':
        status = ai.get('status') if isinstance(ai, dict) else 'invalid'
        reason = ai.get('reason') if isinstance(ai, dict) else None
        raise RuntimeError('inference_IA_' + str(status) + ':' + str(reason)[:200])
    dimensions = ai.get('dimensions')
    if not isinstance(dimensions, dict) or not dimensions:
        raise RuntimeError('IA_dimensions_absentes')
    if any(not isinstance(value, dict) or value.get('decision') not in
           ('match', 'mismatch', 'uncertain', 'not_scored') for value in dimensions.values()):
        raise RuntimeError('IA_dimensions_invalides')
    # Zero match/mismatch is a valid abstention, not a transport/model failure.
    # The persisted review remains a draft, never a scientific validation.
    return dimensions

def process(run_id, client):
    row = api('/internal/analysis/desktop/profile/reviews/run/' + str(run_id))['item']
    snap('lab.profile.row', row)
    ident = row.get('normalized_identity') or normalize_track_identity(row)
    if not ident.get('title'):
        raise RuntimeError('titre_musical_absent')
    if not ident.get('artist'):
        candidate = resolve_missing_artist(ident['title'], build_ai_provider_from_env())
        emit('identity.resolution', {'status': candidate['status'], 'candidate_count': candidate['candidate_count']})
        if candidate['status'] == 'resolved':
            ident = {**ident, 'artist': candidate['artist'], 'method': 'assistant_mb_title_artist_match',
                     'requires_verification': True, 'confidence': None}
            row = {**row, 'artist': candidate['artist'], 'normalized_identity': ident}
        else:
            # Do not invent a performer: public research returns an abstention.
            row = {**row, 'normalized_identity': ident}
    ident = {**ident, 'catalog_duration_ms': duration_from_catalog(row)}
    started = time.perf_counter_ns()
    emit('research.begin', {'identity': ident})
    try:
        research = research_public_sources(ident, NetworkBudget())
    finally:
        emit('research.duration', start_ns=started)
    snap('research.result', research)
    started = time.perf_counter_ns()
    payload = build_review_payload(row, research, min_confidence=.75)
    emit('review.base_payload.duration', start_ns=started)
    snap('review.base_payload', payload)
    started = time.perf_counter_ns()
    # Independent evidence verification. No module results/presets in verifier inputs.
    verification = verify_final_values(row, ident, research)
    snap('profile.final_verification', verification)
    # Research is an integral part of PROFILE, never a hidden opt-in.
    # Missing provider credentials are reported to LAB, never silently skipped.
    investigation = research_each_assertion(row, ident, source_research=research)
    snap('profile.web_investigation', investigation)
    emit('web.investigation.summary', {
        'status': investigation.get('status'),
        'reason': investigation.get('reason'),
        'searched': investigation.get('searched'),
        'web_citations': sum(len(i.get('citation_urls') or []) for i in investigation.get('items') or [])
    })
    verification['web_investigation'] = investigation
    local_web_review = review_web_items(investigation, ident)
    verification['local_web_review'] = local_web_review
    snap('profile.local_web_review', local_web_review)
    emit('web.local_review.summary', {'status': local_web_review.get('status'), 'items': len(local_web_review.get('items') or [])})

    # Retain existing LAB draft transport schema, without claiming AI-generated proof.
    ai = {
        'schema': 'EZStudioLab_assistant.ai-profile-review.v1',
        'status': 'completed',
        'provider': 'independent-evidence-verifier',
        'model': None,
        'confidence': None,
        'summary': 'Vérification indépendante des valeurs musicales finales',
        'dimensions': {
            key: {'decision':'not_scored','confidence':None,
                  'reason':'verification_in_final_assertions'}
            for key in ('genre','instrumentation','lead_vocal','backing_vocals','choir')
        },
        'coverage': {'independent_verification': True}
    }
    payload = enrich_review_payload_with_documentary(payload, row, research)
    payload = enrich_review_payload_with_ai(payload, ai)
    payload.setdefault('comparison', {})['final_verification'] = verification
    payload.setdefault('consensus', {})['final_verification_summary'] = {
        'bon': sum(x['verdict']=='bon' for x in verification['assertions']),
        'faux': sum(x['verdict']=='faux' for x in verification['assertions']),
        'non_trouve': sum(x['verdict']=='non_trouve' for x in verification['assertions'])
    }
    scored_count = 0
    # A completed inference is an advisory DRAFT, never independent validation.
    payload['status'] = 'draft'
    payload['reviewer'] = 'assistant-lab-ui-qwen'
    digest = hashlib.sha256(json.dumps(
        {'ai': ai, 'verification': verification,
         'documentary': payload.get('comparison', {}).get('documentary_catalogue_suggestions'),
         'run_id': run_id}, sort_keys=True, ensure_ascii=True
    ).encode('utf-8')).hexdigest()[:20]
    payload['revision_key'] = 'profile-ui-qwen-' + str(run_id) + '-' + digest
    snap('lab.submit.request', payload)
    started = time.perf_counter_ns()
    try:
        submitted = client.submit_profile_review(payload)
    except Exception as exc:
        emit('lab.submit.error', {'type': type(exc).__name__, 'message': str(exc)}, start_ns=started)
        raise
    emit('lab.submit.duration', start_ns=started)
    snap('lab.submit.response', submitted)
    if not submitted.get('ok'):
        raise RuntimeError('revision_non_persistee_' + str(submitted)[:180])
    return {
        'run_id': run_id,
        'revision': (submitted.get('revision') or {}).get('id'),
        'ai_status': 'completed',
        'review_status': 'draft',
        'scored_count': scored_count,
    }

def once(client):
    requests = api(PATH)['requests']
    if requests:
        print('LAB_PROFILE_IA_PENDING=' + str(len(requests)), flush=True)
    for item in requests:
        rid = int(item['run_id'])
        if not api(PATH + '/' + str(rid) + '/claim', {})['claimed']:
            continue
        status = 'completed'
        message = 'Révision IA créée'
        trace = None
        if enabled():
            try:
                trace = Trace(rid)
            except Exception as trace_exc:
                print('PROFILE_TRACE_INIT_ERROR ' + type(trace_exc).__name__ + ':' + str(trace_exc), flush=True)
        outcome = None
        context = activate(trace) if trace else nullcontext()
        with context:
            try:
                emit('job.claimed', {'run_id': rid, 'claim': True})
                outcome = process(rid, client)
                message = 'Révision IA #' + str(outcome['revision']) + ' enregistrée'
                print(json.dumps(outcome), flush=True)
            except Exception as exc:
                status = 'error'
                message = type(exc).__name__ + ': ' + str(exc)[:750]
                emit('job.error', {'exception': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()})
                print(json.dumps({'run_id': rid, 'status': status, 'reason': message}), flush=True)
            finally:
                try:
                    emit('lab.finish.request', {'status': status, 'message': message})
                    api(PATH + '/' + str(rid) + '/finish', {'status': status, 'message': message})
                except Exception as exc:
                    emit('lab.finish.error', {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()})
                    raise
                finally:
                    if trace:
                        trace.finish({'status': status, 'message': message})
                        try:
                            published = publish_trace(trace, outcome)
                            print('PROFILE_REPORT=' + published, flush=True)
                        except Exception as export_exc:
                            print('PROFILE_REPORT_ERROR=' + type(export_exc).__name__ + ':' + str(export_exc)[:120], flush=True)
                        print('PROFILE_TRACE=' + str(trace.folder), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--poll-seconds', type=int, default=8)
    args = parser.parse_args()
    if enabled():
        purge()
    client = assistant_main._client_from_args(argparse.Namespace(base_url=BASE, token=TOKEN))
    while True:
        try:
            once(client)
        except Exception as exc:
            print('QUEUE_ERROR ' + type(exc).__name__ + ': ' + str(exc)[:500], flush=True)
        if args.once:
            break
        time.sleep(max(5, args.poll_seconds))

if __name__ == '__main__':
    main()
