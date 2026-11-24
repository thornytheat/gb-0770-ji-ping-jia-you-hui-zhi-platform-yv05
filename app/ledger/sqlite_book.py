import sqlite3
from contextlib import contextmanager
from pathlib import Path


class ShiftBook:
    def __init__(self, db_file):
        self.path = Path(db_file)
        self.path.parent.mkdir(exist_ok=True,parents=True)
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS shifts (digest TEXT PRIMARY KEY, manifest TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS stage_rows (digest TEXT NOT NULL REFERENCES shifts(digest), phase TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(digest,phase))')
            db.execute('CREATE TABLE IF NOT EXISTS signatures (digest TEXT PRIMARY KEY REFERENCES shifts(digest), checksum TEXT NOT NULL)')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path,timeout=12)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()
