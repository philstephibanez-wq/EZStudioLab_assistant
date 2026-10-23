"""On-demand Web investigation from Assistant UI. Reads JSON on stdin; emits JSON.
No LAB mutation, no fake reference, no secrets or scientific changes.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_web_investigator import research_assertions
from profile_web_local_review import review_web_items

LABELS = {
    "tempo": "Tempo", "meter": "Mesure", "key": "Tonalité",
    "genre": "Genre", "instrument:0": "Instruments",
    "lead_vocal": "Voix principale", "backing_vocals": "Voix d’accompagnement",
    "vocal_harmonies": "Harmonies vocales", "choir": "Chœurs",
}

def main():
    request = json.load(sys.stdin)
    title = str(request.get("title") or "").strip()
    artist = str(request.get("artist") or "").strip()
    if not title or not artist or len(title) > 180 or len(artist) > 180:
        raise ValueError("titre_et_interprete_requis")
    wanted = list(LABELS)  # Contract PROFILE: never user-selected or partial.
    values = request.get("values") or {}
    if not isinstance(values, dict):
        raise ValueError("valeurs_invalides")
    assertions = []
    for key in wanted:
        if key not in LABELS or any(row["key"] == key for row in assertions):
            continue
        value = str(values.get(key) or "non déterminé").strip()[:120]
        assertions.append({"key": key, "label": LABELS[key], "value": value,
                           "no_lab_proposition": value == "non déterminé"})
    if not assertions:
        raise ValueError("aucun_item_recherchable")
    identity = {"title": title, "artist": artist}
    investigation = research_assertions(assertions, identity)
    ai = review_web_items(investigation, identity)
    # Never expose fetched full page bodies to the browser.
    safe = []
    by_key = {x.get("key"): x for x in ai.get("items", [])}
    for item in investigation.get("items", []):
        safe.append({"key": item.get("key"), "label": LABELS.get(item.get("key")),
                     "value": item.get("value"),
                     "status": item.get("status"), "reason": item.get("reason"),
                     "query": item.get("query"),
                     "sources": [{"url": doc.get("url"), "title": doc.get("title"),
                                  "status": doc.get("status"),
                                  "reason": doc.get("reason") or doc.get("error_type")}
                                 for doc in item.get("documents", [])],
                     "ai": by_key.get(item.get("key"))})
    read_count=sum(sum(doc.get("status")=="read" for doc in item.get("documents",[])) for item in investigation.get("items",[]))
    verified_count=sum(bool((by_key.get(item.get("key")) or {}).get("citations")) for item in investigation.get("items",[]))
    outcome="sources_analyzed" if verified_count else "documents_without_confirmed_values" if read_count else "no_readable_sources"
    print(json.dumps({"ok": True, "schema": "ezs.profile.direct-research.v1",
        "outcome":outcome,"documents_read":read_count,"items_with_citations":verified_count,
        "title": title, "artist": artist,
        "status": investigation.get("status"), "reason": investigation.get("reason"),
        "provider": investigation.get("search_provider"), "items": safe,
        "ocr": investigation.get("ocr_audit"),
        "ai_status": ai.get("status"), "ai_reason": ai.get("reason"),
        "persistence": "none_direct_research"}, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__,
                          "reason": str(exc)[:240]}, ensure_ascii=False))
        sys.exit(1)
