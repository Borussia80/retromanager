import json
import logging
import os
import pickle
import sqlite3
import threading
from pathlib import Path

from _constants import CACHE_DIR, PLATFORMS_CACHE_DB, PLATFORMS_CACHE_FILENAME
from _debug import DebugHelper, DebugType
from models import RomEntry

_log = logging.getLogger("retromanager.platforms")


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

_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS roms_fts USING fts5(
    name, platform,
    content='roms', content_rowid='rowid'
);
CREATE TRIGGER IF NOT EXISTS roms_ai AFTER INSERT ON roms BEGIN
    INSERT INTO roms_fts(rowid, name, platform) VALUES (new.rowid, new.name, new.platform);
END;
"""


class PlatformsHelper:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        is_new_db = not os.path.exists(PLATFORMS_CACHE_DB)
        self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
        self._db.executescript(_SCHEMA)
        if not is_new_db:
            self._integrity_check()
        self._fts_available = self._setup_fts()
        if is_new_db:
            self._migrate_from_json()
        self._migrate_v2()
        if self._fts_available:
            self._rebuild_fts()

    def _integrity_check(self) -> None:
        """Run PRAGMA integrity_check; drop and recreate the DB if corrupted (OBS-003)."""
        try:
            row = self._db.execute("PRAGMA integrity_check").fetchone()
            if row and row[0] != "ok":
                _log.error("integrity_check falhou: %s — recriando DB", row[0])
                self._db.close()
                Path(PLATFORMS_CACHE_DB).unlink(missing_ok=True)
                self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
                self._db.executescript(_SCHEMA)
        except sqlite3.DatabaseError as exc:
            _log.error("DB ilegível (%s) — recriando", exc)
            try:
                self._db.close()
            except Exception as exc:
                _log.warning("Erro ao fechar DB corrompido: %s", exc)
            Path(PLATFORMS_CACHE_DB).unlink(missing_ok=True)
            self._db = sqlite3.connect(PLATFORMS_CACHE_DB, check_same_thread=False)
            self._db.executescript(_SCHEMA)

    def _setup_fts(self) -> bool:
        """Create FTS5 virtual table and populate it if empty. Returns True if FTS5 is available."""
        try:
            self._db.executescript(_FTS_SCHEMA)
            count = self._db.execute("SELECT COUNT(*) FROM roms_fts").fetchone()[0]
            if count == 0:
                self._db.execute(
                    "INSERT INTO roms_fts(rowid, name, platform) SELECT rowid, name, platform FROM roms"
                )
                self._db.commit()
            return True
        except sqlite3.OperationalError:
            return False

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

    def _migrate_v2(self) -> None:
        """Add metadata columns to roms table. Idempotent — safe to call on every startup."""
        with self._lock:
            existing = {row[1] for row in self._db.execute("PRAGMA table_info(roms)")}
            if "description" in existing:
                return
            self._db.executescript("""
                ALTER TABLE roms ADD COLUMN description TEXT    NOT NULL DEFAULT '';
                ALTER TABLE roms ADD COLUMN genre       TEXT    NOT NULL DEFAULT '';
                ALTER TABLE roms ADD COLUMN year        INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE roms ADD COLUMN rating      REAL    NOT NULL DEFAULT 0.0;
                ALTER TABLE roms ADD COLUMN cover_url   TEXT    NOT NULL DEFAULT '';
                ALTER TABLE roms ADD COLUMN region      TEXT    NOT NULL DEFAULT '';
                CREATE INDEX IF NOT EXISTS idx_roms_year   ON roms (year);
                CREATE INDEX IF NOT EXISTS idx_roms_rating ON roms (rating);
                CREATE INDEX IF NOT EXISTS idx_roms_region ON roms (region);
            """)
            self._db.commit()
            _log.info("Schema migrated to v2 (metadata columns added)")

    def _rebuild_fts(self) -> None:
        """Incremental FTS5 rebuild — resync index with roms table without dropping it."""
        try:
            with self._lock:
                self._db.execute("INSERT INTO roms_fts(roms_fts) VALUES('rebuild')")
                self._db.commit()
        except sqlite3.OperationalError as exc:
            _log.warning("FTS rebuild failed (non-fatal): %s", exc)

    def platformsCount(self) -> int:
        with self._lock:
            row = self._db.execute("SELECT COUNT(DISTINCT platform) FROM roms").fetchone()
        return row[0] if row else 0

    def getRomsCount(self, platform_name: str) -> int:
        with self._lock:
            row = self._db.execute(
                "SELECT COUNT(*) FROM roms WHERE platform=?", (platform_name,)
            ).fetchone()
        return row[0] if row else 0

    def getPlatformName(self, index: int) -> str:
        with self._lock:
            row = self._db.execute(
                "SELECT DISTINCT platform FROM roms ORDER BY platform LIMIT 1 OFFSET ?",
                (index,)
            ).fetchone()
        return row[0] if row else ""

    def getPlatforms(self):
        with self._lock:
            return [row[0] for row in self._db.execute(
                "SELECT DISTINCT platform FROM roms ORDER BY platform"
            ).fetchall()]

    def getRomName(self, platform_name: str, index: int) -> str:
        with self._lock:
            row = self._db.execute(
                "SELECT name FROM roms WHERE platform=? ORDER BY name LIMIT 1 OFFSET ?",
                (platform_name, index)
            ).fetchone()
        return row[0] if row else ""

    def getRom(self, platform_name: str, rom_name: str) -> RomEntry | None:
        with self._lock:
            row = self._db.execute(
                "SELECT source_id, file_path, size, md5, crc32, sha1, format "
                "FROM roms WHERE platform=? AND name=?",
                (platform_name, rom_name)
            ).fetchone()
        if row is None:
            return None
        return RomEntry(source_id=row[0], file_path=row[1], size=row[2],
                        md5=row[3], crc32=row[4], sha1=row[5], format=row[6])

    def search_roms(self, platform_name: str, query: str, limit: int = 500) -> list[str]:
        """Return ROM names matching query. Uses FTS5 when available, Python fallback otherwise."""
        query = query.strip()
        if not query:
            with self._lock:
                rows = self._db.execute(
                    "SELECT name FROM roms WHERE platform=? ORDER BY name LIMIT ?",
                    (platform_name, limit)
                ).fetchall()
            return [r[0] for r in rows]

        if self._fts_available:
            tokens = query.lower().split()
            # Escape FTS5 special chars inside quoted phrases so user input
            # like "mario (usa)" or 'zelda"s' doesn't produce syntax errors.
            safe_tokens = [t.replace('"', '""') for t in tokens]
            fts_query = " OR ".join(f'"{t}"*' for t in safe_tokens)
            with self._lock:
                try:
                    # Query roms_fts directly (no JOIN) — the platform column is in the
                    # FTS5 index, so SQLite evaluates it after FTS5 matching without a
                    # full table scan of roms (which caused ~900ms on 40k-row catalogs).
                    rows = self._db.execute(
                        "SELECT name FROM roms_fts "
                        "WHERE roms_fts MATCH ? AND platform=? "
                        "ORDER BY rank LIMIT ?",
                        (fts_query, platform_name, limit)
                    ).fetchall()
                    return [r[0] for r in rows]
                except sqlite3.OperationalError as exc:
                    _log.debug("FTS indisponível, usando fallback Python: %s", exc)

        # Python-side fallback
        with self._lock:
            rows = self._db.execute(
                "SELECT name FROM roms WHERE platform=? ORDER BY name",
                (platform_name,)
            ).fetchall()
        import library_service
        keywords = query.lower().split()
        return [r[0] for r in rows if library_service.rom_matches_filters(r[0], keywords, None)]

    def getRoms(self, platform_name: str):
        with self._lock:
            rows = self._db.execute(
                "SELECT name, source_id, file_path, size, md5, crc32, sha1, format "
                "FROM roms WHERE platform=? ORDER BY name",
                (platform_name,)
            ).fetchall()
        for row in rows:
            yield row[0], RomEntry(source_id=row[1], file_path=row[2], size=row[3],
                                   md5=row[4], crc32=row[5], sha1=row[6], format=row[7])
