"""Tests for mame_names — no Qt required."""
import json
import os
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import mame_names


# ─── _parse_xml ────────────────────────────────────────────────────────────────

class TestParseXml:
    def _write_xml(self, tmp_path, machines):
        lines = ['<?xml version="1.0"?>', "<mameconfig>", "<listxml>"]
        for shortname, desc in machines:
            lines.append(f'  <machine name="{shortname}">')
            lines.append(f"    <description>{desc}</description>")
            lines.append("  </machine>")
        lines += ["</listxml>", "</mameconfig>"]
        p = tmp_path / "mame.xml"
        p.write_text("\n".join(lines), encoding="utf-8")
        return str(p)

    def test_basic_parse(self, tmp_path):
        path = self._write_xml(tmp_path, [("sf2", "Street Fighter II"), ("mk", "Mortal Kombat")])
        result = mame_names._parse_xml(path)
        assert result == {"sf2": "Street Fighter II", "mk": "Mortal Kombat"}

    def test_machine_without_description_skipped(self, tmp_path):
        p = tmp_path / "mame.xml"
        p.write_text(
            '<?xml version="1.0"?><mameconfig><listxml>'
            '<machine name="nodesc"></machine>'
            "</listxml></mameconfig>",
            encoding="utf-8",
        )
        result = mame_names._parse_xml(str(p))
        assert "nodesc" not in result

    def test_empty_xml(self, tmp_path):
        path = self._write_xml(tmp_path, [])
        assert mame_names._parse_xml(path) == {}


# ─── load ──────────────────────────────────────────────────────────────────────

class TestLoad:
    def test_returns_empty_when_no_cache_no_xml(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mame_names, "SEARCH_PATHS", [])
        monkeypatch.setattr(mame_names, "MAME_NAMES_CACHE", str(tmp_path / "nonexistent.json"))
        result = mame_names.load()
        assert result == {}

    def test_loads_existing_cache(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "mame_names.json"
        cache_file.write_text(json.dumps({"sf2": "Street Fighter II"}), encoding="utf-8")
        monkeypatch.setattr(mame_names, "MAME_NAMES_CACHE", str(cache_file))
        result = mame_names.load()
        assert result == {"sf2": "Street Fighter II"}

    def test_corrupted_cache_falls_back_to_empty_without_xml(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "mame_names.json"
        cache_file.write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(mame_names, "MAME_NAMES_CACHE", str(cache_file))
        monkeypatch.setattr(mame_names, "SEARCH_PATHS", [])
        result = mame_names.load()
        assert result == {}


# ─── xml_available / cache_available ───────────────────────────────────────────

class TestAvailability:
    def test_xml_available_false_when_no_paths(self, monkeypatch):
        monkeypatch.setattr(mame_names, "SEARCH_PATHS", [])
        assert not mame_names.xml_available()

    def test_cache_available_false_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mame_names, "MAME_NAMES_CACHE", str(tmp_path / "missing.json"))
        assert not mame_names.cache_available()

    def test_cache_available_true_when_present(self, tmp_path, monkeypatch):
        f = tmp_path / "mame_names.json"
        f.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(mame_names, "MAME_NAMES_CACHE", str(f))
        assert mame_names.cache_available()
