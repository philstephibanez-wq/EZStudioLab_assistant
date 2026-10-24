"""Temporary R38c full LAB catalogue inventory via SQLite read-only mode.
Run locally on MAIN only. No mutations, audio paths, credentials, or LAB jobs.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path

def inventory(database_path):
    path = Path(database_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("database_not_file")
    uri = path.as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=3)
    try:
        connection.execute("PRAGMA query_only=ON")
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('songs','scientific_runs')"
        ).fetchall()
        if {x[0] for x in table} != {"songs", "scientific_runs"}:
            raise ValueError("catalogue_schema_missing")
        rows = connection.execute("""
            SELECT s.id AS song_id, s.title, s.artist,
                   r.id AS run_id, r.state AS state
            FROM songs AS s
            LEFT JOIN scientific_runs AS r ON r.id = (
                SELECT x.id FROM scientific_runs x
                WHERE x.song_id=s.id AND x.item='profile' AND x.state='done'
                ORDER BY x.id DESC LIMIT 1
            )
            ORDER BY s.id
        """).fetchall()
    finally:
        connection.close()
    songs = [{"song_id": int(sid), "title": str(title), "artist": str(artist or ""),
              "run_id": int(run_id) if run_id is not None else None,
              "state": state or "no_completed_profile"} for sid,title,artist,run_id,state in rows]
    return {"schema": "ezstudio.assistant.catalogue-inventory.v1",
            "status": "read_only", "total_songs": len(songs),
            "analyzed_songs": sum(s["run_id"] is not None for s in songs),
            "songs": songs}

def main():
    parser = argparse.ArgumentParser(description="Inspect LAB SQLite without modifications")
    parser.add_argument("database_file", help="Exact MAIN LAB SQLite database file path")
    args = parser.parse_args()
    print(json.dumps(inventory(args.database_file), ensure_ascii=False))
if __name__ == "__main__":
    main()
