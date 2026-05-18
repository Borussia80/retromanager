"""Tests for PlatformsHelper (catalog) — uses in-memory SQLite, no Qt."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture()
def ph(tmp_path, monkeypatch):
    """Return a PlatformsHelper backed by a temp database.

    Patches _platforms module names directly because _platforms does
    `from _constants import ...` at load time, so patching _constants has
    no effect on the already-bound names in _platforms.
    """
    import _platforms
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(_platforms, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(_platforms, "PLATFORMS_CACHE_DB", db_path)
    monkeypatch.setattr(_platforms, "PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json"))
    return _platforms.PlatformsHelper()


def _insert(ph, platform, name, size=0, md5="", crc32="", sha1="", fmt="zip"):
    ph._db.execute(
        "INSERT OR IGNORE INTO roms "
        "(platform, name, source_id, file_path, size, md5, crc32, sha1, format) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (platform, name, "", "", size, md5, crc32, sha1, fmt),
    )
    ph._db.commit()
    ph._setup_fts()


class TestGetRom:
    def test_returns_none_for_missing(self, ph):
        assert ph.getRom("SNES", "Nonexistent") is None

    def test_returns_entry_for_known_rom(self, ph):
        _insert(ph, "SNES", "Mario", size=1024, md5="abc")
        rom = ph.getRom("SNES", "Mario")
        assert rom is not None
        assert rom.md5 == "abc"
        assert rom.size == 1024

    def test_platform_isolated(self, ph):
        _insert(ph, "NES", "Mario", md5="nes")
        _insert(ph, "SNES", "Mario", md5="snes")
        assert ph.getRom("NES", "Mario").md5 == "nes"
        assert ph.getRom("SNES", "Mario").md5 == "snes"


class TestGetRoms:
    def test_empty_platform(self, ph):
        assert list(ph.getRoms("SNES")) == []

    def test_yields_roms_sorted_by_name(self, ph):
        _insert(ph, "SNES", "Zelda")
        _insert(ph, "SNES", "Mario")
        names = [name for name, _ in ph.getRoms("SNES")]
        assert names == sorted(names)

    def test_platform_isolation(self, ph):
        _insert(ph, "NES", "Mario")
        _insert(ph, "SNES", "Zelda")
        nes_names = [n for n, _ in ph.getRoms("NES")]
        assert "Zelda" not in nes_names


class TestGetRomsCount:
    def test_zero_for_empty_platform(self, ph):
        assert ph.getRomsCount("SNES") == 0

    def test_counts_correctly(self, ph):
        _insert(ph, "SNES", "Mario")
        _insert(ph, "SNES", "Zelda")
        _insert(ph, "NES", "Contra")
        assert ph.getRomsCount("SNES") == 2
        assert ph.getRomsCount("NES") == 1


class TestGetPlatforms:
    def test_empty_db(self, ph):
        assert ph.getPlatforms() == []

    def test_returns_distinct_platforms(self, ph):
        _insert(ph, "SNES", "Mario")
        _insert(ph, "SNES", "Zelda")
        _insert(ph, "NES", "Mario")
        platforms = ph.getPlatforms()
        assert platforms == ["NES", "SNES"]

    def test_sorted_alphabetically(self, ph):
        _insert(ph, "SNES", "x")
        _insert(ph, "Atari 2600", "x")
        _insert(ph, "NES", "x")
        assert ph.getPlatforms() == ["Atari 2600", "NES", "SNES"]


class TestSearchRoms:
    def test_empty_query_returns_all(self, ph):
        _insert(ph, "SNES", "Mario")
        _insert(ph, "SNES", "Zelda")
        result = ph.search_roms("SNES", "")
        assert "Mario" in result
        assert "Zelda" in result

    def test_query_filters_by_name(self, ph):
        _insert(ph, "SNES", "Super Mario World")
        _insert(ph, "SNES", "Zelda")
        result = ph.search_roms("SNES", "mario")
        assert "Super Mario World" in result
        assert "Zelda" not in result

    def test_platform_isolated_in_search(self, ph):
        _insert(ph, "NES", "Mario")
        _insert(ph, "SNES", "Mario")
        result = ph.search_roms("NES", "mario")
        assert len([r for r in result]) == 1

    def test_limit_respected(self, ph):
        for i in range(20):
            _insert(ph, "SNES", f"Game {i:02d}")
        result = ph.search_roms("SNES", "", limit=5)
        assert len(result) == 5
