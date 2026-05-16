"""Tests for FavoritesManager — pure Python, no Qt required."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture()
def mgr(tmp_path, monkeypatch):
    """Return a FavoritesManager backed by a temp directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Patch the module-level _FILE constant before import
    import favorites_manager
    monkeypatch.setattr(favorites_manager, "_FILE", str(tmp_path / "favorites.json"))
    return favorites_manager.FavoritesManager()


class TestToggle:
    def test_add_favorite(self, mgr):
        result = mgr.toggle("SNES", "Super Mario World")
        assert result is True

    def test_remove_favorite(self, mgr):
        mgr.toggle("SNES", "Super Mario World")
        result = mgr.toggle("SNES", "Super Mario World")
        assert result is False

    def test_toggle_returns_current_state(self, mgr):
        assert mgr.toggle("NES", "Tetris") is True
        assert mgr.toggle("NES", "Tetris") is False
        assert mgr.toggle("NES", "Tetris") is True


class TestIsFavorite:
    def test_not_favorite_initially(self, mgr):
        assert mgr.is_favorite("SNES", "Zelda") is False

    def test_is_favorite_after_add(self, mgr):
        mgr.toggle("SNES", "Zelda")
        assert mgr.is_favorite("SNES", "Zelda") is True

    def test_not_favorite_after_remove(self, mgr):
        mgr.toggle("SNES", "Zelda")
        mgr.toggle("SNES", "Zelda")
        assert mgr.is_favorite("SNES", "Zelda") is False

    def test_different_platforms_are_independent(self, mgr):
        mgr.toggle("NES", "Mario")
        assert mgr.is_favorite("SNES", "Mario") is False


class TestAll:
    def test_empty_initially(self, mgr):
        assert mgr.all() == []

    def test_returns_added_items(self, mgr):
        mgr.toggle("NES", "Mario")
        mgr.toggle("SNES", "Zelda")
        result = mgr.all()
        assert ("NES", "Mario") in result
        assert ("SNES", "Zelda") in result

    def test_sorted_by_platform_then_name(self, mgr):
        mgr.toggle("SNES", "Zelda")
        mgr.toggle("NES", "Mario")
        mgr.toggle("NES", "Contra")
        result = mgr.all()
        assert result[0] == ("NES", "Contra")
        assert result[1] == ("NES", "Mario")
        assert result[2] == ("SNES", "Zelda")

    def test_removed_items_not_in_all(self, mgr):
        mgr.toggle("NES", "Mario")
        mgr.toggle("NES", "Mario")
        assert ("NES", "Mario") not in mgr.all()


class TestCount:
    def test_zero_initially(self, mgr):
        assert mgr.count() == 0

    def test_increments_on_add(self, mgr):
        mgr.toggle("NES", "Mario")
        assert mgr.count() == 1
        mgr.toggle("SNES", "Zelda")
        assert mgr.count() == 2

    def test_decrements_on_remove(self, mgr):
        mgr.toggle("NES", "Mario")
        mgr.toggle("NES", "Mario")
        assert mgr.count() == 0


class TestPersistence:
    def test_persists_across_instances(self, tmp_path, monkeypatch):
        import favorites_manager
        fpath = str(tmp_path / "favorites.json")
        monkeypatch.setattr(favorites_manager, "_FILE", fpath)

        mgr1 = favorites_manager.FavoritesManager()
        mgr1.toggle("NES", "Mario")

        mgr2 = favorites_manager.FavoritesManager()
        assert mgr2.is_favorite("NES", "Mario")

    def test_corrupted_file_gives_empty_state(self, tmp_path, monkeypatch):
        import favorites_manager
        fpath = str(tmp_path / "favorites.json")
        monkeypatch.setattr(favorites_manager, "_FILE", fpath)
        with open(fpath, "w") as f:
            f.write("not valid json{{")
        mgr = favorites_manager.FavoritesManager()
        assert mgr.count() == 0
