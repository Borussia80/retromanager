"""Tests for SettingsHelper — pure Python, no Qt required."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_settings(tmp_path, monkeypatch):
    """Return a SettingsHelper using tmp_path as the config/cache root.

    Patches _settings module names directly because _settings does
    `from _constants import *` at load time; patching _constants has no
    effect on the already-bound names inside _settings.
    """
    config_dir = tmp_path / ".config" / "retromanager"
    cache_dir = tmp_path / ".cache" / "retromanager"
    settings_file = config_dir / "settings.json"
    download_dir = tmp_path / "ROMs"
    config_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(exist_ok=True)

    import _settings
    monkeypatch.setattr(_settings, "CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(_settings, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(_settings, "SETTINGS_FILE", str(settings_file))
    monkeypatch.setattr(_settings, "DEFAULT_DOWNLOAD_DIR", str(download_dir))
    return _settings.SettingsHelper()


class TestGet:
    def test_returns_known_key(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        assert s.get("cache_expiration") == 30

    def test_unknown_key_raises(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        with pytest.raises(ValueError, match="not found"):
            s.get("nonexistent_key")

    def test_returns_theme_default(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        assert s.get("theme") == "dark"


class TestUpdate:
    def test_updates_known_key(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        s.update(("cache_expiration", 7))
        assert s.get("cache_expiration") == 7

    def test_unknown_key_raises(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        with pytest.raises(ValueError, match="not found"):
            s.update(("nonexistent_key", 99))

    def test_update_does_not_persist_until_write(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        s.update(("cache_expiration", 99))
        # write hasn't been called but the in-memory value should have changed
        assert s.get("cache_expiration") == 99


class TestWrite:
    def test_creates_file_on_write(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        settings_file = tmp_path / ".config" / "retromanager" / "settings.json"
        assert settings_file.exists()

    def test_written_file_is_valid_json(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        settings_file = tmp_path / ".config" / "retromanager" / "settings.json"
        data = json.loads(settings_file.read_text())
        assert isinstance(data, dict)
        assert "cache_expiration" in data


class TestRead:
    def test_reads_existing_file(self, tmp_path, monkeypatch):
        s = _make_settings(tmp_path, monkeypatch)
        s.update(("cache_expiration", 7))
        s.write()
        # Create a second instance (still within the same patched context)
        s2 = _make_settings(tmp_path, monkeypatch)
        assert s2.get("cache_expiration") == 7

    def test_corrupted_file_uses_defaults(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".config" / "retromanager"
        settings_file = config_dir / "settings.json"
        config_dir.mkdir(parents=True)
        (tmp_path / ".cache" / "retromanager").mkdir(parents=True)
        (tmp_path / "ROMs").mkdir()
        settings_file.write_bytes(b"")   # empty → EOFError in json.load

        import _settings
        monkeypatch.setattr(_settings, "CONFIG_DIR", str(config_dir))
        monkeypatch.setattr(_settings, "CACHE_DIR", str(tmp_path / ".cache" / "retromanager"))
        monkeypatch.setattr(_settings, "SETTINGS_FILE", str(settings_file))
        monkeypatch.setattr(_settings, "DEFAULT_DOWNLOAD_DIR", str(tmp_path / "ROMs"))

        s = _settings.SettingsHelper()
        assert s.get("cache_expiration") == 30

    def test_unknown_key_in_file_triggers_fix(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".config" / "retromanager"
        settings_file = config_dir / "settings.json"
        config_dir.mkdir(parents=True)
        (tmp_path / ".cache" / "retromanager").mkdir(parents=True)
        (tmp_path / "ROMs").mkdir()

        cfg = {
            "cache_expiration": 7,
            "check_updates": False,
            "download_path": str(tmp_path / "ROMs"),
            "import_paths": [],
            "organize_by_platform": True,
            "unzip": True,
            "theme": "dark",
            "old_unknown_key": "gone",   # extra key not in defaults
        }
        settings_file.write_text(json.dumps(cfg))

        import _settings
        monkeypatch.setattr(_settings, "CONFIG_DIR", str(config_dir))
        monkeypatch.setattr(_settings, "CACHE_DIR", str(tmp_path / ".cache" / "retromanager"))
        monkeypatch.setattr(_settings, "SETTINGS_FILE", str(settings_file))
        monkeypatch.setattr(_settings, "DEFAULT_DOWNLOAD_DIR", str(tmp_path / "ROMs"))

        s = _settings.SettingsHelper()
        # Known keys should be preserved
        assert s.get("cache_expiration") == 7
        # Unknown key should not be accessible
        with pytest.raises(ValueError):
            s.get("old_unknown_key")
