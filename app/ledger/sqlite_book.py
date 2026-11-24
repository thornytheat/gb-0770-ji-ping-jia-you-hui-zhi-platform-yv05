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
            db.execute('''CREATE TABLE IF NOT EXISTS returns (
                return_id TEXT PRIMARY KEY,
                ticket TEXT NOT NULL,
                truck TEXT NOT NULL,
                weighbill TEXT NOT NULL,
                mass_g INTEGER NOT NULL CHECK(mass_g>0),
                received_at TEXT NOT NULL,
                writeoff TEXT NOT NULL CHECK(writeoff IN ('CONFIRMED','PENDING')),
                reason TEXT,
                voucher TEXT,
                checksum TEXT)''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path,timeout=12)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def immediate(self):
        db = sqlite3.connect(self.path,timeout=12,isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise
        finally:
            db.close()
