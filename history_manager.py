import os
import sqlite3
import time

from _constants import CACHE_DIR

_DB = os.path.join(CACHE_DIR, "history.db")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS launches (
    platform    TEXT NOT NULL,
    rom_name    TEXT NOT NULL,
    last_played INTEGER NOT NULL DEFAULT 0,
    play_count  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (platform, rom_name)
);
CREATE INDEX IF NOT EXISTS idx_launches_last ON launches (last_played DESC);
"""


class HistoryManager:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._db = sqlite3.connect(_DB, check_same_thread=False)
        self._db.executescript(_SCHEMA)

    def record(self, platform: str, rom_name: str) -> None:
        now = int(time.time())
        self._db.execute(
            "INSERT INTO launches (platform, rom_name, last_played, play_count) VALUES (?,?,?,1) "
            "ON CONFLICT(platform, rom_name) DO UPDATE SET "
            "last_played=excluded.last_played, play_count=play_count+1",
            (platform, rom_name, now),
        )
        self._db.commit()

    def recent(self, limit: int = 50) -> list[tuple[str, str, int]]:
        """Return [(platform, rom_name, last_played_ts), ...] newest first."""
        return [
            (row[0], row[1], row[2])
            for row in self._db.execute(
                "SELECT platform, rom_name, last_played FROM launches "
                "ORDER BY last_played DESC LIMIT ?",
                (limit,),
            )
        ]

    def count(self) -> int:
        row = self._db.execute("SELECT COUNT(*) FROM launches").fetchone()
        return row[0] if row else 0
