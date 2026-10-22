"""Discovery-only physical sleeve/booklet evidence (no image interpretation).

Cover Art Archive indexes scans per release; an image existence is never a
musician credit or proof for an individual recording.
"""
from __future__ import annotations
import re
from urllib.parse import urlparse

UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
DOCUMENT_TYPES = {"back", "booklet", "liner", "medium", "spine", "tray", "obi",
                  "inner", "other", "sticker"}


def _safe_url(value):
    if not isinstance(value, str):
        return None
    u = urlparse(value)
    if u.scheme != "https" or u.username or u.password or not u.hostname:
        return None
    if u.hostname.lower() not in {"coverartarchive.org", "archive.org",
                                   "www.archive.org", "ia801000.us.archive.org"}:
        # Metadata occasionally carries different archive.org CDN subdomains.
        if not u.hostname.lower().endswith(".archive.org"):
            return None
    return value


def discover_release_documents(http, release_ids):
    """Return reviewable document links, never extracted musical assertions.

    Bounded to one eligible edition and one network call. Never downloads images.
    No cover-art document is allowed to assert track-specific personnel until
    a later, independently tested extraction proves the credit and its scope.
    """
    result = []
    seen = set()
    for raw in release_ids:
        release_id = str(raw or "").strip()
        if not UUID.fullmatch(release_id) or release_id in seen:
            continue
        seen.add(release_id)
        url = "https://coverartarchive.org/release/" + release_id
        if http.request_count >= http.budget.max_requests_per_item:
            break
        try:
            data = http.get_json(url, retries=0)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for image in (data.get("images") or [])[:24]:
            if not isinstance(image, dict) or image.get("approved") is not True:
                continue
            types = [str(t).casefold() for t in image.get("types") or []]
            if not (set(types) & DOCUMENT_TYPES or image.get("back") is True):
                continue
            document_url = _safe_url(image.get("image"))
            if not document_url:
                continue
            result.append({
                "release_id": release_id, "document_url": document_url,
                "types": types, "scope": "release_unverified",
                "credit_text": None, "track_attribution": None,
                "evidence_eligible": False,
            })
        break
    return result[:16]
