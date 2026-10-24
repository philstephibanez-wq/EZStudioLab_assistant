"""R38 independent five-song rotation; no LAB writes or silent recycling."""
from __future__ import annotations
import json
import os
from pathlib import Path

def choose_unseen(rows, used_ids, count=5):
    """Pick the first five distinct untested catalogue songs, otherwise refuse."""
    latest = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid, rid = row.get("song_id"), row.get("run_id")
        if type(sid) is not int or sid <= 0 or type(rid) is not int or rid <= 0:
            continue
        if not str(row.get("title") or "").strip():
            continue
        if sid not in latest or rid > latest[sid]["run_id"]:
            latest[sid] = row
    fresh = [latest[sid] for sid in sorted(latest) if sid not in set(used_ids)]
    return {"status": "selected" if len(fresh) >= count else "insufficient_unseen_songs",
            "selected": fresh[:count] if len(fresh) >= count else [],
            "population_count": len(latest), "unseen_count": len(fresh),
            "used_count_in_population": len(latest) - len(fresh)}

def load_history(path):
    p = Path(path)
    if not p.exists():
        return set()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != "ezstudio.assistant.sample-history.v1":
        raise ValueError("invalid_sample_history")
    ids = raw.get("song_ids")
    if not isinstance(ids, list) or any(type(x) is not int or x <= 0 for x in ids):
        raise ValueError("invalid_sample_ids")
    return set(ids)

def commit_history(path, previous_ids, selected_ids):
    """Atomic single-process replacement; caller commits only after successful batch."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps({"schema": "ezstudio.assistant.sample-history.v1",
                          "song_ids": sorted(set(previous_ids) | set(selected_ids))},
                         ensure_ascii=True) + "\n"
    import tempfile
    fd, name = tempfile.mkstemp(dir=str(p.parent), prefix=".sample-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as writer:
            writer.write(content)
            writer.flush()
            os.fsync(writer.fileno())
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)
