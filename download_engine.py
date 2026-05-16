"""
Download engine v2 — concurrent downloads with exponential retry (FEAT-001).

Drop-in replacement for DownloadWorker: same signals, same usage in mainwindow.py.
"""

import logging
import threading

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

from _tools import DownloadWorker
from _settings import SettingsHelper
from _platforms import PlatformsHelper

_log = logging.getLogger("retromanager.download_engine")


class DownloadEngine(QObject):
    """Manages up to MAX_CONCURRENT parallel downloads with exponential retry."""

    MAX_CONCURRENT = 3
    MAX_RETRIES    = 3
    RETRY_DELAYS   = [5, 30, 120]   # seconds per attempt

    # Same signal surface as DownloadWorker for drop-in compatibility
    startedItem   = pyqtSignal(str, str, int, int)   # platform, rom_name, slot, total
    progress      = pyqtSignal(int, int, float)       # bytes_done, total_bytes, speed
    completedItem = pyqtSignal(str, str)               # platform, rom_name
    failedItem    = pyqtSignal(str, str, str)          # platform, rom_name, error
    cancelled     = pyqtSignal()
    finished      = pyqtSignal()

    def __init__(self, settings: SettingsHelper, platforms: PlatformsHelper,
                 queue_items: list[tuple[str, str]],
                 max_concurrent: int = MAX_CONCURRENT):
        super().__init__(None)
        self._settings = settings
        self._platforms = platforms
        self._pending: list[tuple[str, str]] = list(queue_items)
        self._max_concurrent = max_concurrent
        self._total = len(queue_items)
        self._completed_count = 0
        self._retry_counts: dict[str, int] = {}
        self._active_threads: dict[str, QThread] = {}
        self._active_workers: dict[str, DownloadWorker] = {}
        self._lock = threading.Lock()
        self._global_cancel = threading.Event()
        self._all_done = False

    def cancel(self):
        self._global_cancel.set()
        with self._lock:
            for worker in self._active_workers.values():
                worker.cancel()

    def run(self):
        """Called from the engine's own thread (started by mainwindow). Fills initial slots."""
        if not self._pending:
            self.finished.emit()
            return
        # _start_next_batch must run on the main thread because it creates QObjects.
        # Use QTimer to schedule it there.
        QTimer.singleShot(0, self._start_next_batch)

    def _start_next_batch(self):
        """Fill available concurrency slots from the pending queue."""
        with self._lock:
            slots = self._max_concurrent - len(self._active_threads)
            to_start = self._pending[:slots]
            self._pending = self._pending[slots:]

        for platform, rom_name in to_start:
            self._start_worker(platform, rom_name)

    def _start_worker(self, platform: str, rom_name: str):
        if self._global_cancel.is_set():
            return

        cancel_event = threading.Event()

        worker = DownloadWorker(self._settings, self._platforms, [(platform, rom_name)])
        worker._cancel = cancel_event

        thread = QThread()
        worker.moveToThread(thread)

        with self._lock:
            slot = self._completed_count + len(self._active_threads) + 1
            self._active_threads[rom_name] = thread
            self._active_workers[rom_name] = worker

        thread.started.connect(worker.run)
        worker.startedItem.connect(
            lambda p, r, _c, _t, s=slot: self.startedItem.emit(p, r, s, self._total)
        )
        worker.progress.connect(self.progress)
        worker.completedItem.connect(self._on_worker_completed)
        worker.failedItem.connect(self._on_worker_failed)
        worker.cancelled.connect(self._on_worker_cancelled)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda rn=rom_name: self._on_thread_done(rn))

        thread.start()
        _log.debug("started download slot for %s", rom_name)

    def _on_worker_completed(self, platform: str, rom_name: str):
        self._completed_count += 1
        self._retry_counts.pop(rom_name, None)
        with self._lock:
            self._active_workers.pop(rom_name, None)
        self.completedItem.emit(platform, rom_name)

    def _on_worker_failed(self, platform: str, rom_name: str, error: str):
        retries = self._retry_counts.get(rom_name, 0)
        with self._lock:
            self._active_workers.pop(rom_name, None)

        if not self._global_cancel.is_set() and retries < self.MAX_RETRIES:
            delay_ms = self.RETRY_DELAYS[retries] * 1000
            self._retry_counts[rom_name] = retries + 1
            _log.info("retry %d/%d for %s in %ds", retries + 1, self.MAX_RETRIES,
                      rom_name, self.RETRY_DELAYS[retries])
            QTimer.singleShot(delay_ms, lambda p=platform, r=rom_name: self._retry(p, r))
        else:
            self._retry_counts.pop(rom_name, None)
            self.failedItem.emit(platform, rom_name, error)

    def _retry(self, platform: str, rom_name: str):
        with self._lock:
            # Put the item back at the front of the pending queue
            self._pending.insert(0, (platform, rom_name))
        self._start_next_batch()

    def _on_worker_cancelled(self):
        self.cancelled.emit()

    def _on_thread_done(self, rom_name: str):
        with self._lock:
            self._active_threads.pop(rom_name, None)

        if self._global_cancel.is_set():
            with self._lock:
                remaining = len(self._active_threads)
            if remaining == 0 and not self._all_done:
                self._all_done = True
                self.finished.emit()
            return

        with self._lock:
            has_pending = bool(self._pending)
            active = len(self._active_threads)

        if has_pending:
            self._start_next_batch()
        elif active == 0 and not self._all_done:
            self._all_done = True
            self.finished.emit()
