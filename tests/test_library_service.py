"""Tests for library_service — pure Python, no Qt required."""
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import library_service
from models import RomEntry


class _FakeSettings:
    """Minimal duck-type of SettingsHelper used by library_service."""

    def __init__(self, download_path, import_paths=()):
        self._d = {"download_path": download_path, "import_paths": list(import_paths)}

    def get(self, key):
        return self._d[key]


# ─── scan_downloaded ───────────────────────────────────────────────────────────

class TestScanDownloaded:
    def test_empty_dir(self, tmp_path):
        s = _FakeSettings(str(tmp_path))
        assert library_service.scan_downloaded(s) == set()

    def test_finds_files_in_base(self, tmp_path):
        (tmp_path / "Sonic.zip").write_bytes(b"x")
        (tmp_path / "Mario.nes").write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        result = library_service.scan_downloaded(s)
        assert "Sonic" in result
        assert "Mario" in result

    def test_finds_files_in_platform_subdir(self, tmp_path):
        sub = tmp_path / "SNES"
        sub.mkdir()
        (sub / "Zelda.zip").write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        result = library_service.scan_downloaded(s, platform="SNES")
        assert "Zelda" in result

    def test_finds_files_in_import_paths(self, tmp_path):
        import_dir = tmp_path / "external"
        import_dir.mkdir()
        (import_dir / "DonkeyKong.zip").write_bytes(b"x")
        dl_dir = tmp_path / "downloads"
        dl_dir.mkdir()
        s = _FakeSettings(str(dl_dir), import_paths=[str(import_dir)])
        result = library_service.scan_downloaded(s)
        assert "DonkeyKong" in result

    def test_nonexistent_dir_is_ignored(self, tmp_path):
        s = _FakeSettings(str(tmp_path / "nonexistent"))
        assert library_service.scan_downloaded(s) == set()

    def test_subdirs_not_included_as_stems(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        s = _FakeSettings(str(tmp_path))
        assert library_service.scan_downloaded(s) == set()


# ─── find_rom_file ─────────────────────────────────────────────────────────────

class TestFindRomFile:
    def test_finds_extracted_file_in_base(self, tmp_path):
        rom = tmp_path / "Sonic.nes"
        rom.write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        assert library_service.find_rom_file(s, "Sonic", None) == str(rom)

    def test_prefers_extracted_over_archive(self, tmp_path):
        extracted = tmp_path / "Mario.nes"
        archive = tmp_path / "Mario.zip"
        extracted.write_bytes(b"x")
        archive.write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        result = library_service.find_rom_file(s, "Mario", None)
        assert result == str(extracted)

    def test_falls_back_to_zip(self, tmp_path):
        archive = tmp_path / "Zelda.zip"
        archive.write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        assert library_service.find_rom_file(s, "Zelda", None) == str(archive)

    def test_finds_in_platform_subdir_first(self, tmp_path):
        sub = tmp_path / "SNES"
        sub.mkdir()
        in_sub = sub / "DK.snes"
        in_base = tmp_path / "DK.snes"
        in_sub.write_bytes(b"x")
        in_base.write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        assert library_service.find_rom_file(s, "DK", "SNES") == str(in_sub)

    def test_returns_none_when_not_found(self, tmp_path):
        s = _FakeSettings(str(tmp_path))
        assert library_service.find_rom_file(s, "missing", None) is None

    def test_skips_part_files(self, tmp_path):
        (tmp_path / "Game.zip.part").write_bytes(b"x")
        s = _FakeSettings(str(tmp_path))
        assert library_service.find_rom_file(s, "Game.zip", None) is None


# ─── rom_matches_filters ───────────────────────────────────────────────────────

class TestRomMatchesFilters:
    def test_no_filters_always_matches(self):
        assert library_service.rom_matches_filters("Any ROM", [], None)

    def test_keyword_match(self):
        assert library_service.rom_matches_filters("Sonic the Hedgehog (USA)", ["sonic"], None)

    def test_keyword_no_match(self):
        assert not library_service.rom_matches_filters("Mario Bros (USA)", ["sonic"], None)

    def test_multiple_keywords_all_required(self):
        assert library_service.rom_matches_filters("Sonic Spinball (USA)", ["sonic", "usa"], None)
        assert not library_service.rom_matches_filters("Sonic Spinball (USA)", ["sonic", "europe"], None)

    def test_region_filter_match(self):
        assert library_service.rom_matches_filters("Sonic (USA)", [], "USA")

    def test_region_filter_no_match(self):
        assert not library_service.rom_matches_filters("Sonic (Europe)", [], "USA")

    def test_keyword_matches_shortname_fallback(self):
        assert library_service.rom_matches_filters("sf2", ["street fighter"], None, shortname="street fighter ii")

    def test_case_insensitive(self):
        assert library_service.rom_matches_filters("SONIC THE HEDGEHOG", ["sonic"], None)

    def test_fuzzy_subsequence_match(self):
        assert library_service.rom_matches_filters("Sonic the Hedgehog", ["snic"], None)

    def test_fuzzy_no_match(self):
        assert not library_service.rom_matches_filters("Mario Bros (USA)", ["sonic"], None)

    def test_fuzzy_requires_min_3_chars(self):
        assert not library_service.rom_matches_filters("Mario Bros", ["sz"], None)


# ─── build_rom_summary ─────────────────────────────────────────────────────────

class TestBuildRomSummary:
    _rom_data = RomEntry(size=1048576, format="zip", md5="abc", crc32="def", sha1="ghi")

    def test_contains_rom_name(self):
        result = library_service.build_rom_summary("NES", "Super Mario (USA)", self._rom_data)
        assert "Super Mario (USA)" in result

    def test_contains_platform(self):
        result = library_service.build_rom_summary("NES", "Super Mario (USA)", self._rom_data)
        assert "NES" in result

    def test_extracts_tags_from_parens(self):
        result = library_service.build_rom_summary("NES", "Game (USA) (Rev 1)", self._rom_data)
        assert "USA" in result
        assert "Rev 1" in result

    def test_size_formatter_called(self):
        formatted = []
        def fmt(n):
            formatted.append(n)
            return f"{n}B"
        library_service.build_rom_summary("NES", "Game", self._rom_data, size_formatter=fmt)
        assert formatted == [1048576]

    def test_no_size_formatter_falls_back_to_str(self):
        result = library_service.build_rom_summary("NES", "Game", self._rom_data)
        assert "1048576" in result

    def test_missing_size_key(self):
        result = library_service.build_rom_summary("NES", "Game", RomEntry())
        assert "0" in result
