"""Point de traitement XPS, appelé par LAB/orchestrateur, sans claim ni requête LAB."""
from __future__ import annotations
import hmac
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from profile_assertions_contract import ITEMS, build_assertions, validate_verdicts
from profile_web_investigator import research_assertions
from profile_document_consultation import consult
from profile_tesseract_runtime import resolve_tesseract, booklet_ocr_enabled
from web_status import DEFAULT_TOKEN_FILE, _read_dpapi_token

WEB_KEYS = dict(zip(ITEMS, (
    "duration", "tempo", "meter", "key", "genre", "instrument:0",
    "lead_vocal", "backing_vocals", "vocal_harmonies", "choir",
)))

def verify(payload):
    request = build_assertions(payload)
    rows = [{"key": WEB_KEYS[key], "value": request["items"][key],
             "label": key} for key in ITEMS]
    investigation = research_assertions(
        rows, {"title": request["title"], "artist": request["artist"]}
    )
    by_key = {
        row["key"]: row for row in (investigation.get("items") or [])
        if isinstance(row, dict) and row.get("key") in WEB_KEYS.values()
    }
    reviews = {}
    for key in ITEMS:
        row = by_key.get(WEB_KEYS[key], {})
        candidate = row.get("evidence_review") or {}
        absent = request["items"][key] is None
        # Page titre/artiste != preuve de correspondance à l'enregistrement.
        reviews[key] = {
            "verdict": "sans_valeur_lab" if absent else "non_trouve",
            "reference_value": candidate.get("reference_value"),
            "reason": "Valeur LAB absente" if absent else (
                candidate.get("reason") or "Identité de l'enregistrement non confirmée"
            ),
            "evidence": [],
            "confidence_pct": None,
            "consulted_urls": [
                d["url"] for d in (row.get("documents") or [])
                if isinstance(d, dict) and d.get("status") == "read"
                and isinstance(d.get("url"), str)
            ],
            "technical_status": row.get("status", "not_searched"),
            # Evidence candidates are NOT recording-level confirmations.
            "proposed_verdict": candidate.get("proposed_verdict")
                if candidate.get("proposed_verdict") in ("bon", "faux") else None,
            "references": [
                {"url": ref["url"], "reference_value": ref.get("reference_value"),
                 "verdict": ref.get("verdict"), "attribution": ref.get("attribution")}
                for ref in (candidate.get("references") or [])
                if isinstance(ref, dict) and isinstance(ref.get("url"), str)
                and ref["url"].startswith("https://")
            ],
        }
    result = {
        "schema": "ezstudio.profile.review.v1",
        "expertise_type": request["expertise_type"],
        "analysis_id": request["analysis_id"],
        "preset_id": request["preset_id"],
        "identity_confirmed": False,
        "reviews": reviews,
        "technical_status": investigation.get("status"),
        "technical_errors": investigation.get("technical_errors", 0),
    }
    validate_verdicts(request, result)
    # Evidence and verdicts are finalized before advisory AI is consulted.
    result["ai_consultation"] = consult(
        {"title":request["title"],"artist":request["artist"]}, reviews)
    result["tool_audit"] = {
        "qwen":result["ai_consultation"]["status"],
        "ocr":"not_executed_no_scan_supplied",
        "ocr_enabled":booklet_ocr_enabled(),
        "translation":"qwen_advisory_notes_only",
        "document_search":investigation.get("status"),
    }
    return result

def process(envelope, token_reader=_read_dpapi_token):
    if not isinstance(envelope, dict):
        raise ValueError("invalid_envelope")
    supplied = envelope.get("_auth_token")
    stored = token_reader(DEFAULT_TOKEN_FILE)
    if not isinstance(supplied, str) or not stored or not hmac.compare_digest(supplied, stored):
        raise PermissionError("unauthorized")
    request = {k: v for k, v in envelope.items() if k != "_auth_token"}
    return verify(request)

def main():
    try:
        envelope = json.load(sys.stdin)
        answer = process(envelope)
        print(json.dumps(answer, ensure_ascii=False, allow_nan=False))
        return 0
    except PermissionError:
        print('{"error":"unauthorized"}')
        return 3
    except ValueError as exc:
        print(json.dumps({"error": "invalid_request", "reason": str(exc)[:120]}))
        return 2
    except Exception as exc:
        print(json.dumps({"error": "processing_failed", "type": type(exc).__name__}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
