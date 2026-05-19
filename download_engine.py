"""
Download engine v2 — QThreadPool-based concurrent downloads with retry.

Each ROM is a _DownloadTask (QRunnable). QThreadPool owns the thread lifecycle;
no manual QThread creation, no GC crashes.
"""

import logging
import threading

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal

from _tools import DownloadWorker
from _settings import SettingsHelper
from _platforms import PlatformsHelper

_log = logging.getLogger("retromanager.download_engine")

_MAX_CONCURRENT = 3
_MAX_RETRIES    = 3
_RETRY_DELAYS   = [5, 30, 120]   # seconds per attempt


class _DownloadTask(QRunnable):
    """Single-ROM download unit. QThreadPool manages the thread lifecycle."""

    class _Signals(QObject):
        started   = pyqtSignal(str, str, int, int)   # platform, rom_name, slot, total
        progress  = pyqtSignal(int, int, float)       # bytes_done, total_bytes, speed
        completed = pyqtSignal(str, str)               # platform, rom_name
        failed    = pyqtSignal(str, str, str)          # platform, rom_name, error

    def __init__(self, settings: SettingsHelper, platforms: PlatformsHelper,
                 platform: str, rom_name: str, slot: int, total: int,
                 cancel: threading.Event):
        super().__init__()
        self.setAutoDelete(False)   # DownloadEngine keeps a ref in _tasks
        self.signals    = _DownloadTask._Signals()
        self._settings  = settings
        self._platforms = platforms
        self._platform  = platform
        self._rom_name  = rom_name
        self._slot      = slot
        self._total     = total
        self._cancel    = cancel

    def run(self):
        if self._cancel.is_set():
            return
        self.signals.started.emit(self._platform, self._rom_name, self._slot, self._total)
        try:
            worker = DownloadWorker(self._settings, self._platforms, [], self._cancel)
            worker.progress.connect(self.signals.progress)
            path = worker._download(self._platform, self._rom_name)
            if self._settings.get('unzip'):
                worker._unzip(path)
            self.signals.completed.emit(self._platform, self._rom_name)
        except InterruptedError:
            pass   # user cancelled — engine handles cleanup via _cancel flag
        except Exception as e:
            self.signals.failed.emit(self._platform, self._rom_name, str(e))


class DownloadEngine(QObject):
    """Manages up to _MAX_CONCURRENT parallel downloads with exponential retry.

    Drop-in replacement for the old DownloadWorker: same signals, same usage in
    mainwindow.py. Uses QThreadPool internally so no QThread is ever created or
    destroyed manually.
    """

    # Same signal surface as old DownloadWorker for drop-in compatibility.
    startedItem   = pyqtSignal(str, str, int, int)
    progress      = pyqtSignal(int, int, float)
    completedItem = pyqtSignal(str, str)
    failedItem    = pyqtSignal(str, str, str)
    cancelled     = pyqtSignal()
    finished      = pyqtSignal()

    def __init__(self, settings: SettingsHelper, platforms: PlatformsHelper,
                 queue_items: list[tuple[str, str]],
                 max_concurrent: int = _MAX_CONCURRENT):
        super().__init__(None)
        self._settings  = settings
        self._platforms = platforms
        self._pending   = list(queue_items)
        self._total     = len(queue_items)
        self._active    = 0   # tasks running OR waiting to retry
        self._started   = 0   # ever-started count for slot display
        self._cancel    = threading.Event()
        self._tasks: set[_DownloadTask] = set()    # keeps Python refs alive
        self._retry_counts: dict[str, int] = {}
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(max_concurrent)

    def cancel(self):
        self._cancel.set()
        self.cancelled.emit()

    def run(self):
        """Called from the engine's QThread. Schedules first batch on event loop."""
        if not self._pending:
            self.finished.emit()
            return
        QTimer.singleShot(0, self._fill_slots)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fill_slots(self):
        """Start tasks until concurrency limit is reached or queue is empty."""
        while (self._pending
               and self._active < self._pool.maxThreadCount()
               and not self._cancel.is_set()):
            platform, rom_name = self._pending.pop(0)
            self._active += 1
            self._started += 1
            self._launch(platform, rom_name, self._started)

    def _launch(self, platform: str, rom_name: str, slot: int):
        task = _DownloadTask(self._settings, self._platforms,
                             platform, rom_name, slot, self._total, self._cancel)
        task.signals.started.connect(self.startedItem)
        task.signals.progress.connect(self.progress)
        task.signals.completed.connect(lambda p, r, t=task: self._on_completed(t, p, r))
        task.signals.failed.connect(lambda p, r, e, t=task: self._on_failed(t, p, r, e))
        self._tasks.add(task)
        self._pool.start(task)
        _log.debug("launched slot %d for %s", slot, rom_name)

    def _on_completed(self, task: _DownloadTask, platform: str, rom_name: str):
        self._tasks.discard(task)
        self._retry_counts.pop(rom_name, None)
        self._active -= 1
        self.completedItem.emit(platform, rom_name)
        self._fill_slots_or_finish()

    def _on_failed(self, task: _DownloadTask, platform: str, rom_name: str, error: str):
        self._tasks.discard(task)
        retries = self._retry_counts.get(rom_name, 0)
        if not self._cancel.is_set() and retries < _MAX_RETRIES:
            delay_ms = _RETRY_DELAYS[retries] * 1000
            self._retry_counts[rom_name] = retries + 1
            _log.info("retry %d/%d for %s in %ds",
                      retries + 1, _MAX_RETRIES, rom_name, _RETRY_DELAYS[retries])
            # _active stays incremented while this slot waits to retry.
            # This prevents finished from being emitted too early.
            QTimer.singleShot(delay_ms, lambda p=platform, r=rom_name: self._retry(p, r))
            self._fill_slots()   # fill other open slots while this one waits
        else:
            self._retry_counts.pop(rom_name, None)
            self._active -= 1
            self.failedItem.emit(platform, rom_name, error)
            self._fill_slots_or_finish()

    def _retry(self, platform: str, rom_name: str):
        if self._cancel.is_set():
            self._active -= 1
            self._fill_slots_or_finish()
            return
        self._started += 1
        self._launch(platform, rom_name, self._started)

    def _fill_slots_or_finish(self):
        if self._pending and not self._cancel.is_set():
            self._fill_slots()
        elif self._active == 0:
            self.finished.emit()
