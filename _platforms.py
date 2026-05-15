import json
import os
import pickle
import sqlite3

from _constants import CACHE_DIR, PLATFORMS_CACHE_DB, PLATFORMS_CACHE_FILENAME
from _debug import DebugHelper, DebugType
from models import RomEntry


_SCHEMA = """
CREATE TABLE IF NOT EXISTS roms (
    platform  TEXT NOT NULL,
    name      TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    file_path TEXT NOT NULL DEFAULT '',
    size      INTEGER NOT NULL DEFAULT 0,
    md5       TEXT NOT NULL DEFAULT '',
    crc32     TEXT NOT NULL DEFAULT '',
    sha1      TEXT NOT NULL DEFAULT '',
    format    TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (platform, name)
);
CREATE INDEX IF NOT EXISTS idx_roms_platform ON roms (platform);
"""


class PlatformsHelper:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        is_new_db = not os.path.exists(PLATFORMS_CACHE_DB)
        self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
        self._db.executescript(_SCHEMA)
        if is_new_db:
            self._migrate_from_json()

    def _migrate_from_json(self):
        if not os.path.exists(PLATFORMS_CACHE_FILENAME):
            return
        data = None
        try:
            with open(PLATFORMS_CACHE_FILENAME, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
        except json.JSONDecodeError:
            try:
                with open(PLATFORMS_CACHE_FILENAME, 'rb') as fp:
                    data = pickle.load(fp)
            except Exception as e:
                DebugHelper.print(DebugType.TYPE_ERROR, f"Migration failed: {e}", "PLATFORMS")
                return
        except Exception as e:
            DebugHelper.print(DebugType.TYPE_ERROR, f"Migration failed: {e}", "PLATFORMS")
            return

        if not isinstance(data, dict):
            return

        rows = []
        for platform, roms in data.items():
            if not isinstance(roms, dict):
                continue
            for name, d in roms.items():
                if not isinstance(d, dict):
                    continue
                rows.append((
                    platform, name,
                    d.get('source_id', ''), d.get('file_path', ''),
                    int(d.get('size', 0)),
                    d.get('md5', ''), d.get('crc32', ''),
                    d.get('sha1', ''), d.get('format', ''),
                ))
        self._db.executemany("INSERT OR IGNORE INTO roms VALUES (?,?,?,?,?,?,?,?,?)", rows)
        self._db.commit()
        DebugHelper.print(DebugType.TYPE_INFO,
                          f"Migrated {len(rows)} ROMs from JSON to SQLite", "PLATFORMS")

    def platformsCount(self) -> int:
        row = self._db.execute("SELECT COUNT(DISTINCT platform) FROM roms").fetchone()
        return row[0] if row else 0

    def getRomsCount(self, platform_name: str) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) FROM roms WHERE platform=?", (platform_name,)
        ).fetchone()
        return row[0] if row else 0

    def getPlatformName(self, index: int) -> str:
        rows = self._db.execute(
            "SELECT DISTINCT platform FROM roms ORDER BY platform"
        ).fetchall()
        return rows[index][0]

    def getPlatforms(self):
        return (
            row[0] for row in
            self._db.execute("SELECT DISTINCT platform FROM roms ORDER BY platform")
        )

    def getRomName(self, platform_name: str, index: int) -> str:
        rows = self._db.execute(
            "SELECT name FROM roms WHERE platform=? ORDER BY name", (platform_name,)
        ).fetchall()
        return rows[index][0]

    def getRom(self, platform_name: str, rom_name: str) -> RomEntry | None:
        row = self._db.execute(
            "SELECT source_id, file_path, size, md5, crc32, sha1, format "
            "FROM roms WHERE platform=? AND name=?",
            (platform_name, rom_name)
        ).fetchone()
        if row is None:
            return None
        return RomEntry(source_id=row[0], file_path=row[1], size=row[2],
                        md5=row[3], crc32=row[4], sha1=row[5], format=row[6])

    def getRoms(self, platform_name: str):
        for row in self._db.execute(
            "SELECT name, source_id, file_path, size, md5, crc32, sha1, format "
            "FROM roms WHERE platform=? ORDER BY name",
            (platform_name,)
        ):
            yield row[0], RomEntry(source_id=row[1], file_path=row[2], size=row[3],
                                   md5=row[4], crc32=row[5], sha1=row[6], format=row[7])
