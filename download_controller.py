from PyQt6.QtCore import QObject, Qt, QThread, QTimer
from PyQt6.QtWidgets import QMessageBox

from _debug import DebugHelper, DebugType
from download_engine import DownloadEngine
from download_queue import DownloadQueue
from error_dialog import DownloadErrorDialog
from platform_icons import fmt_count


class DownloadController(QObject):
    """Coordinates queue, engine, panel, and download-related UI state."""

    def __init__(self, window, settings, platforms, notifier, panel):
        super().__init__(window)
        self._window = window
        self._settings = settings
        self._platforms = platforms
        self._notifier = notifier
        self.panel = panel
        self.queue = DownloadQueue(window)

        self._thread = None
        self._worker = None
        self._total_count = 0
        self._completed_count = 0
        self._failed = False
        self._paused = False
        self._active_rom_name = None

    def restore_queue_to_panel(self):
        for _, rom_name in self.queue.items():
            self.panel.add_item(rom_name)
        self.update_status_text()

    def handle_detail_download(self, platform: str, rom_name: str):
        added = self.queue.add(platform, [rom_name])
        if added:
            self.panel.add_item(rom_name)
        self.update_status_text()
        self.launch_downloads(notify_if_running=False)

    def handle_download_by_name(self, platform: str, rom_name: str):
        self.queue.add(platform, [rom_name])
        self.update_status_text()
        self.launch_downloads(notify_if_running=False)

    def update_status_text(self):
        count = self.queue.getTotalCount()
        is_running = bool(self._thread and self._thread.isRunning())
        if count > 0:
            self._window.statusbar_queue.setText(f"<a href='#'>{fmt_count(count)} na fila</a>")
        else:
            self._window.statusbar_queue.setText("")
        self.panel.set_downloading(is_running)
        if not is_running:
            self.panel._btn_start.setEnabled(count > 0)
        self._window._update_queue_tab_label()

    def launch_downloads(self, notify_if_running: bool = True):
        if self._thread and self._thread.isRunning():
            if notify_if_running:
                QMessageBox.information(
                    self._window, "Download em andamento", "Um download já está em andamento."
                )
            return
        if self.queue.getTotalCount() == 0:
            QMessageBox.information(
                self._window, "Fila de download", "Nenhum item na fila de download."
            )
            return

        items = self.queue.items()
        self._total_count = len(items)
        self._completed_count = 0
        self._failed = False
        self._paused = False
        self._active_rom_name = None

        self.panel.clear()
        for _, rom_name in items:
            self.panel.add_item(rom_name)
        self.panel.set_downloading(True)
        self.panel._btn_start.setEnabled(False)

        self._thread = QThread(self._window)
        self._worker = DownloadEngine(self._settings, self._platforms, items)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.startedItem.connect(self._on_started_item)
        self._worker.progress.connect(self._on_progress)
        self._worker.completedItem.connect(self._on_completed_item)
        self._worker.failedItem.connect(self._on_failed_item)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        self._window._tab_queue.setChecked(True)

    def cancel(self):
        if self._worker:
            self._worker.cancel()

    def retry(self, rom_name: str):
        if not (self._thread and self._thread.isRunning()):
            self.launch_downloads()

    def shutdown(self):
        if self._thread and self._thread.isRunning():
            self.cancel()
            self._thread.quit()
            if not self._thread.wait(5000):
                self._thread.terminate()

    def _on_started_item(self, platform: str, rom_name: str, current: int, total: int):
        self._active_rom_name = rom_name
        self.panel.start_item(rom_name)
        self._window.statusBar().showMessage(f"Baixando {current}/{total}: [{platform}] {rom_name}")

    def _on_progress(self, rom_name: str, bytes_done: int, total_bytes: int, speed: float):
        self.panel.update_progress(rom_name, bytes_done, total_bytes, speed)

    def _on_completed_item(self, platform: str, rom_name: str):
        self._completed_count += 1
        self.queue.remove(platform, rom_name)
        self.panel.complete_item(rom_name)
        self.update_status_text()
        self._notifier.send("Download concluído", f"{rom_name} está pronto para jogar.")

        for i in range(self._window.tw_romsList.rowCount()):
            item = self._window.tw_romsList.item(i, 0)
            shortname = (item.data(Qt.ItemDataRole.UserRole + 3) or item.text()) if item else None
            if item and shortname == rom_name:
                item.setData(Qt.ItemDataRole.UserRole + 1, True)
                self._window.tw_romsList.viewport().update()
                break
        if self._window._detail_panel._rom_name == rom_name:
            self._window._detail_panel.sync_downloaded(True)

    def _on_failed_item(self, platform: str, rom_name: str, error: str):
        self._failed = True
        self.panel.fail_item(rom_name, error)
        DebugHelper.print(
            DebugType.TYPE_ERROR,
            f"Download failed [{platform}] {rom_name}: {error}",
            "downloader",
        )
        dlg = DownloadErrorDialog(rom_name, platform, error, parent=self._window)
        if dlg.exec() == DownloadErrorDialog.DialogCode.Accepted:
            QTimer.singleShot(0, self.launch_downloads)

    def _on_cancelled(self):
        self._paused = True
        if self._active_rom_name:
            self.panel.cancel_item(self._active_rom_name)

    def _on_thread_finished(self):
        was_paused = self._paused
        self._thread = None
        self._worker = None
        self._active_rom_name = None
        self._paused = False
        self.update_status_text()
        self._window._tab_detail.setChecked(True)
        if was_paused:
            self._window.statusBar().showMessage("Download pausado. Clique ▶ para continuar.", 5000)
        elif not self._failed:
            self._window.statusBar().showMessage(
                f"{fmt_count(self._completed_count)} baixados.", 5000
            )
