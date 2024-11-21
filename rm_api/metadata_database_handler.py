import sqlite3
from functools import lru_cache
from typing import Union
import threading


class MetadataDatabaseHandler:
    def __init__(self, database_file='metadata.db'):
        self._database_file = database_file
        self._initialized = False
        self._lock = threading.RLock()

    def _initialize_database(self):
        with sqlite3.connect(self._database_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    hash TEXT PRIMARY KEY,
                    contents BLOB
                )
            ''')
            conn.commit()
        self._initialized = True

    @lru_cache(maxsize=5000)
    def get_hash(self, file_hash: str) -> Union[bytes, None]:
        # with self._lock:
        if not self._initialized:
            self._initialize_database()
        with sqlite3.connect(self._database_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT contents FROM metadata WHERE hash = ?', (file_hash,))
            result = cursor.fetchone()
            return result[0] if result else None

    def check_hash(self, file_hash: str) -> bool:
        with self._lock:
            if not self._initialized:
                self._initialize_database()
            with sqlite3.connect(self._database_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM metadata WHERE hash = ?', (file_hash,))
                return cursor.fetchone() is not None

    def set_hash(self, file_hash: str, data: bytes):
        with self._lock:
            if not self._initialized:
                self._initialize_database()
            with sqlite3.connect(self._database_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (hash, contents)
                    VALUES (?, ?)
                ''', (file_hash, data))
                conn.commit()
