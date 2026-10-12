from __future__ import annotations

from pathlib import Path
import json
from typing import Any


SEPARATORS = (" - ", " – ", " — ")


def normalize_track_identity(row: dict[str, Any]) -> dict[str, Any]:
    raw_title = str(row.get("title") or "").strip()
    raw_artist = str(row.get("artist") or "").strip()

    if raw_artist:
        return {
            "title": raw_title,
            "artist": raw_artist,
            "raw_title": raw_title,
            "raw_artist": raw_artist,
            "method": "catalog",
            "confidence": 1.0,
            "requires_verification": False,
        }

    for separator in SEPARATORS:
        if separator not in raw_title:
            continue
        title, artist = raw_title.rsplit(separator, 1)
        title = title.strip()
        artist = artist.strip()
        if title and artist:
            return {
                "title": title,
                "artist": artist,
                "raw_title": raw_title,
                "raw_artist": raw_artist,
                "method": "title_suffix_heuristic",
                "confidence": 0.65,
                "requires_verification": True,
            }

    return {
        "title": raw_title,
        "artist": raw_artist,
        "raw_title": raw_title,
        "raw_artist": raw_artist,
        "method": "catalog_incomplete",
        "confidence": 0.25,
        "requires_verification": True,
    }


def profile_review_queue_snapshot(client: Any, *, limit: int = 100) -> dict[str, Any]:
    jobs = client.profile_review_queue(limit=limit)
    normalized = []
    for row in jobs:
        item = dict(row)
        item["normalized_identity"] = normalize_track_identity(item)
        normalized.append(item)

    return {
        "schema": "EZStudioLab_assistant.profile-review-queue.v1",
        "review_execution_enabled": False,
        "automatic_preset_promotion_enabled": False,
        "count": len(normalized),
        "reviews": normalized,
    }


def load_review_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("profile_review_payload_must_be_object")
    return payload
