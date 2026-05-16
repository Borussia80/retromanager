"""Tests for HistoryManager — pure Python, no Qt required."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture()
def mgr(tmp_path, monkeypatch):
    """Return a HistoryManager backed by a temp database."""
    import history_manager
    monkeypatch.setattr(history_manager, "_DB", str(tmp_path / "history.db"))
    return history_manager.HistoryManager()


class TestRecord:
    def test_record_increases_count(self, mgr):
        assert mgr.count() == 0
        mgr.record("SNES", "Zelda")
        assert mgr.count() == 1

    def test_record_same_game_twice_is_single_entry(self, mgr):
        mgr.record("NES", "Mario")
        mgr.record("NES", "Mario")
        assert mgr.count() == 1

    def test_different_games_are_separate_entries(self, mgr):
        mgr.record("NES", "Mario")
        mgr.record("NES", "Tetris")
        assert mgr.count() == 2

    def test_record_updates_timestamp(self, mgr, monkeypatch):
        import history_manager
        call_count = [0]

        def _fake_time():
            call_count[0] += 1
            return float(call_count[0])

        monkeypatch.setattr(history_manager.time, "time", _fake_time)
        mgr.record("NES", "Mario")
        t1 = mgr.recent(1)[0][2]
        mgr.record("NES", "Mario")
        t2 = mgr.recent(1)[0][2]
        assert t2 > t1


class TestRecent:
    def test_empty_initially(self, mgr):
        assert mgr.recent() == []

    def test_returns_recorded_games(self, mgr):
        mgr.record("SNES", "Zelda")
        result = mgr.recent()
        assert len(result) == 1
        assert result[0][0] == "SNES"
        assert result[0][1] == "Zelda"

    def test_ordered_newest_first(self, mgr, monkeypatch):
        import history_manager
        call_count = [0]

        def _fake_time():
            call_count[0] += 1
            return float(call_count[0])

        monkeypatch.setattr(history_manager.time, "time", _fake_time)
        mgr.record("NES", "Mario")
        mgr.record("SNES", "Zelda")
        recent = mgr.recent()
        assert recent[0][1] == "Zelda"
        assert recent[1][1] == "Mario"

    def test_limit_respected(self, mgr):
        for i in range(10):
            mgr.record("NES", f"Game{i}")
        assert len(mgr.recent(limit=3)) == 3

    def test_default_limit_is_50(self, mgr):
        for i in range(60):
            mgr.record("NES", f"Game{i}")
        assert len(mgr.recent()) == 50


class TestCount:
    def test_zero_initially(self, mgr):
        assert mgr.count() == 0

    def test_increments_per_unique_game(self, mgr):
        mgr.record("NES", "Mario")
        mgr.record("NES", "Mario")
        mgr.record("SNES", "Zelda")
        assert mgr.count() == 2
