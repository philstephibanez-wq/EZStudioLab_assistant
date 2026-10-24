"""R38d temporary sample integration tests."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

script=Path(__file__).resolve().parents[1]/"scripts"/"r38d-five-from-catalogue.py"
spec=importlib.util.spec_from_file_location("r38d_sampler",script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class R38d(unittest.TestCase):
    def test_three_disjoint_batches_with_seeded_history(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"lab.sqlite"
            cx=sqlite3.connect(db)
            try:
                cx.execute("CREATE TABLE songs(id INTEGER PRIMARY KEY,title TEXT,artist TEXT)")
                cx.execute("CREATE TABLE scientific_runs(id INTEGER PRIMARY KEY,song_id INTEGER,item TEXT,state TEXT)")
                for i in range(1,40):
                    cx.execute("INSERT INTO songs VALUES(?,?,?)",(i,"Song "+str(i),""))
                    cx.execute("INSERT INTO scientific_runs VALUES(?,?,?,?)",(i+100,i,"profile","done"))
                cx.commit()
            finally:
                cx.close()
            before=db.read_bytes()
            history=Path(td)/"history.json"
            batches=[]
            for _ in range(3):
                cat,selection,used=module.prepare(db,history)
                self.assertEqual(cat["total_songs"],39)
                self.assertEqual(selection["status"],"selected")
                ids={row["song_id"] for row in selection["selected"]}
                self.assertTrue(ids.isdisjoint(module.PREVIOUSLY_TESTED))
                self.assertTrue(all(ids.isdisjoint(previous) for previous in batches))
                module.commit_history(history,used,ids)
                batches.append(ids)
            self.assertEqual(db.read_bytes(),before)
            self.assertEqual(len(module.load_history(history)),25)

    def test_unwritten_preview_does_not_create_history(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"lab.sqlite"
            cx=sqlite3.connect(db)
            try:
                cx.execute("CREATE TABLE songs(id INTEGER PRIMARY KEY,title TEXT,artist TEXT)")
                cx.execute("CREATE TABLE scientific_runs(id INTEGER PRIMARY KEY,song_id INTEGER,item TEXT,state TEXT)")
                for i in range(1,40):
                    cx.execute("INSERT INTO songs VALUES(?,?,?)",(i,"Song "+str(i),""))
                    cx.execute("INSERT INTO scientific_runs VALUES(?,?,?,?)",(i+100,i,"profile","done"))
                cx.commit()
            finally:
                cx.close()
            history=Path(td)/"history.json"
            module.prepare(db,history)
            self.assertFalse(history.exists())

if __name__=="__main__":
    unittest.main()
