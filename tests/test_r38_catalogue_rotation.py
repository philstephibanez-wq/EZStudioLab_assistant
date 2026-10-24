"""R38: five different songs per documented sample batch."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_catalogue_rotation import choose_unseen, load_history, commit_history

class R38(unittest.TestCase):
    def rows(self, n):
        return [{"song_id": i, "run_id": 100 + i, "title": "Song " + str(i)}
                for i in range(1, n + 1)]

    def test_disjoint_batches(self):
        used = set()
        for _ in range(3):
            result = choose_unseen(self.rows(16), used)
            self.assertEqual(result["status"], "selected")
            ids = {r["song_id"] for r in result["selected"]}
            self.assertEqual(len(ids), 5)
            self.assertFalse(ids & used)
            used |= ids
        self.assertEqual(choose_unseen(self.rows(16), used)["status"], "insufficient_unseen_songs")

    def test_duplicate_run_latest(self):
        rows = self.rows(5) + [{"song_id": 1, "run_id": 200, "title": "New Song"}]
        selected = choose_unseen(rows, set())["selected"]
        self.assertEqual(next(x for x in selected if x["song_id"] == 1)["run_id"], 200)

    def test_atomic_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            self.assertEqual(load_history(path), set())
            commit_history(path, set(), {3, 4})
            self.assertEqual(load_history(path), {3, 4})
            commit_history(path, {3, 4}, {5})
            self.assertEqual(load_history(path), {3, 4, 5})

    def test_bad_history_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            path.write_text('{"schema":"bad","song_ids":[1]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_history(path)

if __name__ == "__main__":
    unittest.main()
