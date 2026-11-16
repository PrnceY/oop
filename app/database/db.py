"""Database wrapper around sqlite3 (swap this class to move to MySQL/PostgreSQL)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class Database:
    def __init__(self, path):
        self._path = str(path)
        self._shared = None
        # An in-memory database disappears when its connection closes,
        # so keep one connection open for it (used in tests).
        if self._path == ":memory:":
            self._shared = self._open()

    def _open(self):
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self):
        """Commit on success, roll back on error."""
        conn = self._shared if self._shared is not None else self._open()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if conn is not self._shared:
                conn.close()

    def init_schema(self):
        with self.connection() as conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
