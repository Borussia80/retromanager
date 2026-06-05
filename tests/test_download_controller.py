from unittest.mock import MagicMock

import pytest


class _FakeQueue:
    def __init__(self, _window):
        self.add_calls = []
        self._items = []

    def add(self, platform, rom_names):
        self.add_calls.append((platform, list(rom_names)))
        self._items.extend((platform, rom_name) for rom_name in rom_names)
        return len(rom_names)

    def items(self):
        return list(self._items)

    def getTotalCount(self):
        return len(self._items)


def _make_controller(monkeypatch, qtbot):
    import importlib
    import importlib.util
    import sys
    import types

    existing_pyqt = sys.modules.get("PyQt6")
    if existing_pyqt is not None and getattr(existing_pyqt, "__spec__", None) is None:
        pytest.skip("PyQt6 real não está disponível neste ambiente de teste")
    if importlib.util.find_spec("PyQt6") is None:
        pytest.skip("PyQt6 não está disponível neste ambiente de teste")

    for mod in (
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtNetwork",
        "PyQt6.sip",
    ):
        sys.modules.pop(mod, None)
    import PyQt6  # noqa: F401

    fake_download_queue = types.ModuleType("download_queue")
    fake_download_queue.DownloadQueue = _FakeQueue
    monkeypatch.setitem(sys.modules, "download_queue", fake_download_queue)
    sys.modules.pop("download_controller", None)
    download_controller = importlib.import_module("download_controller")
    monkeypatch.setattr(download_controller, "DownloadQueue", _FakeQueue)
    from PyQt6.QtWidgets import QMainWindow

    window = QMainWindow()
    qtbot.addWidget(window)
    window.statusbar_queue = MagicMock()
    window._update_queue_tab_label = MagicMock()
    window._tab_queue = MagicMock()
    window._tab_detail = MagicMock()
    panel = MagicMock()
    notifier = MagicMock()
    return download_controller.DownloadController(window, MagicMock(), MagicMock(), notifier, panel)


def test_handle_detail_download_autostarts_without_running_alert(monkeypatch, qtbot):
    controller = _make_controller(monkeypatch, qtbot)
    controller.launch_downloads = MagicMock()

    controller.handle_detail_download("Nintendo - NES", "Super Mario Bros.")

    assert controller.queue.add_calls == [("Nintendo - NES", ["Super Mario Bros."])]
    controller.panel.add_item.assert_called_once_with("Super Mario Bros.")
    controller.launch_downloads.assert_called_once_with(notify_if_running=False)


def test_handle_download_by_name_autostarts_without_running_alert(monkeypatch, qtbot):
    controller = _make_controller(monkeypatch, qtbot)
    controller.launch_downloads = MagicMock()

    controller.handle_download_by_name("Nintendo - SNES", "Super Metroid")

    assert controller.queue.add_calls == [("Nintendo - SNES", ["Super Metroid"])]
    controller.launch_downloads.assert_called_once_with(notify_if_running=False)
