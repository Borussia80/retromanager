"""QUAL-003 — Memory leak test for platform navigation.

Requires: pytest-qt, objgraph
Install: pip install pytest-qt objgraph

Run with:
    pytest tests/integration/test_memory.py -v

This test needs a real display server (X11 / Wayland). Skip on headless CI by setting:
    SKIP_GUI_TESTS=1
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_GUI_TESTS") == "1",
    reason="GUI tests skipped (SKIP_GUI_TESTS=1)",
)


@pytest.fixture
def mock_settings():
    from unittest.mock import MagicMock
    s = MagicMock()
    s.get.return_value = ""
    return s


@pytest.fixture
def mock_updater():
    from unittest.mock import MagicMock
    u = MagicMock()
    u.currentVersionString.return_value = "2.3.0"
    return u


@pytest.fixture
def mock_platforms(tmp_path):
    """In-memory PlatformsHelper with a handful of test platforms."""
    import sqlite3
    from unittest.mock import patch

    db_path = str(tmp_path / "test.db")
    with patch("_platforms.PLATFORMS_CACHE_DB", db_path), \
         patch("_platforms.CACHE_DIR", str(tmp_path)), \
         patch("_platforms.PLATFORMS_CACHE_FILENAME", str(tmp_path / "legacy.json")):
        from _platforms import PlatformsHelper
        helper = PlatformsHelper()

    # Seed with two platforms
    rows = [(f"Nintendo - NES", f"ROM {i}", "", "", 1024, "", "", "", "zip") for i in range(50)]
    rows += [(f"Nintendo - SNES", f"ROM {i}", "", "", 2048, "", "", "", "zip") for i in range(30)]
    helper._db.executemany(
        """
        INSERT OR IGNORE INTO roms
        (platform, name, source_id, file_path, size, md5, crc32, sha1, format)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    helper._db.commit()
    return helper


def test_platform_navigation_no_leak(qtbot, mock_settings, mock_updater, mock_platforms):
    """Navigate between platforms 10 times; QTableWidgetItem count must not grow."""
    try:
        import objgraph
    except ImportError:
        pytest.skip("objgraph not installed — run: pip install objgraph")

    from _updater import UpdaterHelper
    from unittest.mock import patch, MagicMock

    with patch("mainwindow.RetroArchHelper", return_value=MagicMock(detected=False)), \
         patch("mainwindow.LutrisHelper", return_value=MagicMock(detected=False)):
        from mainwindow import MainWindow
        window = MainWindow(mock_settings, mock_updater, mock_platforms)
        qtbot.addWidget(window)
        window.show()

    platforms = mock_platforms.getPlatforms()
    if len(platforms) < 2:
        pytest.skip("Not enough platforms to navigate")

    # Warm up — first navigation may create cached objects
    for p in platforms[:2]:
        items = window.lw_platforms.findItems(p, __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.MatchFlag.MatchContains)
        if items:
            window.lw_platforms.setCurrentItem(items[0])
            qtbot.wait(100)

    baseline = objgraph.count("QTableWidgetItem")

    for _ in range(10):
        for p in platforms[:2]:
            items = window.lw_platforms.findItems(
                p, __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.MatchFlag.MatchContains
            )
            if items:
                window.lw_platforms.setCurrentItem(items[0])
                qtbot.wait(50)

    final = objgraph.count("QTableWidgetItem")
    assert final <= baseline + 20, (
        f"QTableWidgetItem leak detected: baseline={baseline}, final={final}"
    )
