"""Tests for _thumbnail_evict.evict_lru — no Qt required."""
import os
import sys
import time


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import _thumbnail_evict


def _write_png(path: str, size: int = 1024):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x00" * size)


class TestEvictLru:
    def test_no_eviction_when_under_limit(self, tmp_path):
        _write_png(str(tmp_path / "sys" / "a.png"), 100)
        _write_png(str(tmp_path / "sys" / "b.png"), 100)
        deleted = _thumbnail_evict.evict_lru(str(tmp_path), max_bytes=10_000, max_count=100)
        assert deleted == 0

    def test_evicts_by_count(self, tmp_path):
        for i in range(5):
            _write_png(str(tmp_path / "sys" / f"{i}.png"), 100)
            time.sleep(0.01)  # ensure distinct mtimes
        deleted = _thumbnail_evict.evict_lru(str(tmp_path), max_bytes=10_000, max_count=3)
        remaining = list((tmp_path / "sys").glob("*.png"))
        assert deleted == 2
        assert len(remaining) == 3

    def test_evicts_oldest_first(self, tmp_path):
        old = tmp_path / "sys" / "old.png"
        new = tmp_path / "sys" / "new.png"
        _write_png(str(old), 100)
        time.sleep(0.02)
        _write_png(str(new), 100)
        _thumbnail_evict.evict_lru(str(tmp_path), max_bytes=10_000, max_count=1)
        assert not old.exists()
        assert new.exists()

    def test_evicts_by_size(self, tmp_path):
        for i in range(3):
            _write_png(str(tmp_path / "sys" / f"{i}.png"), 1000)
            time.sleep(0.01)
        deleted = _thumbnail_evict.evict_lru(str(tmp_path), max_bytes=1500, max_count=100)
        assert deleted >= 1
        remaining = list((tmp_path / "sys").glob("*.png"))
        total = sum(p.stat().st_size for p in remaining)
        assert total <= 1500

    def test_ignores_non_png_files(self, tmp_path):
        txt = tmp_path / "sys" / "readme.txt"
        os.makedirs(txt.parent, exist_ok=True)
        txt.write_bytes(b"hello")
        deleted = _thumbnail_evict.evict_lru(str(tmp_path), max_bytes=0, max_count=0)
        assert deleted == 0
        assert txt.exists()

    def test_empty_cache_returns_zero(self, tmp_path):
        assert _thumbnail_evict.evict_lru(str(tmp_path)) == 0
