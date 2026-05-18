"""Tests for _platforms.py schema migration (_migrate_v2 and _rebuild_fts)."""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_v1_db(path: str) -> sqlite3.Connection:
    """Create a v1 database (without metadata columns)."""
    db = sqlite3.connect(path)
    db.executescript("""
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
        INSERT INTO roms (platform, name, size) VALUES ('Nintendo - NES', 'Super Mario Bros', 40960);
        INSERT INTO roms (platform, name, size) VALUES ('Nintendo - NES', 'Duck Tales', 32768);
    """)
    db.commit()
    return db


class TestMigrateV2:
    def test_migrate_v2_adds_columns(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = _make_v1_db(db_path)
        db.close()

        with patch("_platforms.PLATFORMS_CACHE_DB", db_path), \
             patch("_platforms.CACHE_DIR", str(tmp_path)), \
             patch("_platforms.PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json")):
            from _platforms import PlatformsHelper
            helper = PlatformsHelper()

        existing = {
            row[1] for row in helper._db.execute("PRAGMA table_info(roms)")
        }
        for col in ("description", "genre", "year", "rating", "cover_url", "region"):
            assert col in existing, f"Column '{col}' missing after migration"

    def test_migrate_v2_idempotent(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = _make_v1_db(db_path)
        db.close()

        with patch("_platforms.PLATFORMS_CACHE_DB", db_path), \
             patch("_platforms.CACHE_DIR", str(tmp_path)), \
             patch("_platforms.PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json")):
            from _platforms import PlatformsHelper
            helper = PlatformsHelper()
            # Running twice must not raise
            helper._migrate_v2()
            helper._migrate_v2()

        # Schema should still be intact
        existing = {row[1] for row in helper._db.execute("PRAGMA table_info(roms)")}
        assert "description" in existing

    def test_existing_data_preserved(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = _make_v1_db(db_path)
        db.close()

        with patch("_platforms.PLATFORMS_CACHE_DB", db_path), \
             patch("_platforms.CACHE_DIR", str(tmp_path)), \
             patch("_platforms.PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json")):
            from _platforms import PlatformsHelper
            helper = PlatformsHelper()

        count = helper._db.execute(
            "SELECT COUNT(*) FROM roms WHERE platform='Nintendo - NES'"
        ).fetchone()[0]
        assert count == 2, "Existing ROMs must survive schema migration"

    def test_rebuild_fts_runs_without_error(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = _make_v1_db(db_path)
        db.close()

        with patch("_platforms.PLATFORMS_CACHE_DB", db_path), \
             patch("_platforms.CACHE_DIR", str(tmp_path)), \
             patch("_platforms.PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json")):
            from _platforms import PlatformsHelper
            helper = PlatformsHelper()
            if helper._fts_available:
                helper._rebuild_fts()   # must not raise
