"""R38c SQLite read-only inventory, temporary validation only."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

script=Path(__file__).resolve().parents[1]/"scripts"/"r38c-main-catalogue-inventory.py"
spec=importlib.util.spec_from_file_location("r38c_inventory",script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class R38c(unittest.TestCase):
    def test_entire_catalogue_with_missing_analysis(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"catalog.sqlite"
            with sqlite3.connect(db) as cx:
                cx.execute("CREATE TABLE songs(id INTEGER PRIMARY KEY,title TEXT,artist TEXT)")
                cx.execute("CREATE TABLE scientific_runs(id INTEGER PRIMARY KEY,song_id INTEGER,item TEXT,state TEXT)")
                cx.executemany("INSERT INTO songs(id,title,artist) VALUES(?,?,?)",
                               [(i,"Song "+str(i),"") for i in range(1,24)])
                cx.execute("INSERT INTO scientific_runs VALUES(15,1,'profile','done')")
                cx.execute("INSERT INTO scientific_runs VALUES(16,1,'profile','done')")
            before=db.read_bytes()
            data=module.inventory(db)
            self.assertEqual(data["total_songs"],23)
            self.assertEqual(data["analyzed_songs"],1)
            self.assertEqual(data["songs"][0]["run_id"],16)
            self.assertEqual(before,db.read_bytes())

    def test_missing_database_never_created(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"absent.sqlite"
            with self.assertRaises(FileNotFoundError):
                module.inventory(db)
            self.assertFalse(db.exists())

if __name__ == "__main__":
    unittest.main()
