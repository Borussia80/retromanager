"""
Automated screenshot capture for design review.
Run from the project root: python3 make_screenshots.py
"""
import os, sys
os.environ.setdefault('DEBUG', '0')
os.environ['DISPLAY'] = os.environ.get('DISPLAY', ':0')

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QListWidgetItem
from PyQt6.QtCore import QResource

from _constants import ICONS_DIR, RESOURCES_FILE
from _settings import SettingsHelper
from _updater import UpdaterHelper
from _platforms import PlatformsHelper
from theme import DARK_THEME
from mainwindow import MainWindow

OUT = os.path.join(os.path.dirname(__file__), 'screenshots')
os.makedirs(OUT, exist_ok=True)


def grab(widget, name):
    px = widget.grab()
    path = os.path.join(OUT, f"{name}.png")
    px.save(path)
    print(f"  saved: {path}")


def run():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    _icon = QIcon()
    for _size in (16, 32, 48, 64, 128, 256, 512):
        _icon.addPixmap(QPixmap(f"{ICONS_DIR}/icon_{_size}.png"))
    app.setWindowIcon(_icon)
    QResource.registerResource(RESOURCES_FILE)

    settings  = SettingsHelper()
    updater   = UpdaterHelper()
    platforms = PlatformsHelper()

    w = MainWindow(settings, updater, platforms)
    w.resize(1280, 760)
    w.show()
    app.processEvents()

    steps = []

    def step(fn):
        steps.append(fn)

    # ── 1. Empty state ─────────────────────────────────────────
    @step
    def _():
        grab(w, '01_empty_state')

    # ── 2. Select first available platform → ROM list ──────────
    @step
    def _():
        for i in range(w.lw_platforms.count()):
            item = w.lw_platforms.item(i)
            if item and item.flags() & Qt.ItemFlag.ItemIsEnabled:
                key = item.data(Qt.ItemDataRole.UserRole)
                if key and key != '_FAVORITES_':
                    w.lw_platforms.setCurrentItem(item)
                    w._onListwidgetSelectionChanged(item)
                    app.processEvents()
                    break
        grab(w, '02_rom_list')

    # ── 3. Filter bar active (type a search) ───────────────────
    @step
    def _():
        w.le_filter.setText("Mario")
        app.processEvents()
        w._applyTableFilter()
        app.processEvents()
        grab(w, '03_search_filter')
        w.le_filter.clear()
        app.processEvents()

    # ── 4. Grid view ───────────────────────────────────────────
    @step
    def _():
        w.pb_view_grid.setChecked(True)
        w._switch_view('grid')
        app.processEvents()
        grab(w, '04_grid_view')

    # ── 5. Back to list, region filter ─────────────────────────
    @step
    def _():
        w.pb_view_list.setChecked(True)
        w._switch_view('list')
        w.pb_usa.setChecked(True)
        app.processEvents()
        w._applyTableFilter()
        app.processEvents()
        grab(w, '05_region_filter_usa')
        w.pb_all.setChecked(True)
        app.processEvents()

    # ── 6. Favorites view (empty) ──────────────────────────────
    @step
    def _():
        fav_item = w.lw_platforms.item(0)
        w.lw_platforms.setCurrentItem(fav_item)
        w._onListwidgetSelectionChanged(fav_item)
        app.processEvents()
        grab(w, '06_favorites_empty')

    # ── 7. Favorites with one entry ────────────────────────────
    @step
    def _():
        # Add first ROM of first platform as favorite
        for i in range(w.lw_platforms.count()):
            item = w.lw_platforms.item(i)
            if item and item.flags() & Qt.ItemFlag.ItemIsEnabled:
                key = item.data(Qt.ItemDataRole.UserRole)
                if key and key != '_FAVORITES_':
                    w.lw_platforms.setCurrentItem(item)
                    w._onListwidgetSelectionChanged(item)
                    app.processEvents()
                    if w.tw_romsList.rowCount() > 0:
                        rom_item = w.tw_romsList.item(0, 0)
                        if rom_item:
                            w._favorites.toggle(key, rom_item.text())
                            rom_item.setData(Qt.ItemDataRole.UserRole + 2, True)
                            if hasattr(w, '_fav_widget'):
                                w._fav_widget.update_count(w._favorites.count())
                    break
        fav_item = w.lw_platforms.item(0)
        w.lw_platforms.setCurrentItem(fav_item)
        w._onListwidgetSelectionChanged(fav_item)
        app.processEvents()
        grab(w, '07_favorites_with_entry')
        # Clean up: remove the test favorite
        for (plat, rom) in list(w._favorites.all()):
            w._favorites.toggle(plat, rom)
        if hasattr(w, '_fav_widget'):
            w._fav_widget.update_count(0)

    # ── 8. Download panel with items ───────────────────────────
    @step
    def _():
        # Re-select a platform and add some ROMs to queue
        for i in range(w.lw_platforms.count()):
            item = w.lw_platforms.item(i)
            if item and item.flags() & Qt.ItemFlag.ItemIsEnabled:
                key = item.data(Qt.ItemDataRole.UserRole)
                if key and key != '_FAVORITES_':
                    w.lw_platforms.setCurrentItem(item)
                    w._onListwidgetSelectionChanged(item)
                    app.processEvents()
                    names = [
                        w.tw_romsList.item(r, 0).text()
                        for r in range(min(4, w.tw_romsList.rowCount()))
                        if w.tw_romsList.item(r, 0)
                    ]
                    for n in names:
                        w.download_queue.add(key, [n])
                        w.download_panel.add_item(n)
                    w._updateStatusbarQueueText()
                    app.processEvents()
                    break
        grab(w, '08_download_queue_panel')
        # Clear fake queue
        for item_w in list(w.download_panel._items.values()):
            item_w.deleteLater()
        w.download_panel._items.clear()
        w.download_panel._refresh_badge()
        w.download_queue.queue_dict.clear()
        w.download_queue._save()

    # ── 9. Technical columns visible ───────────────────────────
    @step
    def _():
        w.actionToggleTechnical.setChecked(True)
        w._toggleTechnicalColumns(True)
        app.processEvents()
        grab(w, '09_technical_columns')
        w.actionToggleTechnical.setChecked(False)
        w._toggleTechnicalColumns(False)
        app.processEvents()

    # ── 10. About dialog ───────────────────────────────────────
    @step
    def _():
        w.aboutDialog.show()
        app.processEvents()
        grab(w.aboutDialog, '10_about_dialog')
        w.aboutDialog.hide()

    # ── 11. Options/Settings dialog ────────────────────────────
    @step
    def _():
        w.optionsDialog.show()
        app.processEvents()
        grab(w.optionsDialog, '11_options_dialog')
        w.optionsDialog.hide()

    # ── 12. Download error dialog ──────────────────────────────
    @step
    def _():
        from error_dialog import DownloadErrorDialog
        dlg = DownloadErrorDialog(
            "Super Mario World (USA)",
            "Nintendo - SNES",
            "Connection timed out after 60s",
            parent=w,
        )
        dlg.show()
        app.processEvents()
        grab(dlg, '12_download_error_dialog')
        dlg.hide()
        dlg.deleteLater()

    # ── 13. Hash result dialog — all OK ────────────────────────
    @step
    def _():
        from error_dialog import HashResultDialog
        results = {
            "MD5":   ("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4", "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"),
            "SHA1":  ("da39a3ee5e6b4b0d3255bfef95601890afd80709", "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
            "CRC32": ("d87f7e0c", "d87f7e0c"),
        }
        dlg = HashResultDialog("/home/user/ROMs/Nintendo - SNES/Super Mario World (USA).smc", results, parent=w)
        dlg.show()
        app.processEvents()
        grab(dlg, '13_hash_ok_dialog')
        dlg.hide()
        dlg.deleteLater()

    # ── 14. Hash result dialog — mismatch ──────────────────────
    @step
    def _():
        from error_dialog import HashResultDialog
        results = {
            "MD5":   ("deadbeefdeadbeefdeadbeefdeadbeef", "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"),
            "SHA1":  ("da39a3ee5e6b4b0d3255bfef95601890afd80709", "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
            "CRC32": ("d87f7e0c", "d87f7e0c"),
        }
        dlg = HashResultDialog("/home/user/ROMs/Nintendo - SNES/Super Mario World (USA).smc", results, parent=w)
        dlg.show()
        app.processEvents()
        grab(dlg, '14_hash_fail_dialog')
        dlg.hide()
        dlg.deleteLater()

    # ── 15. Opções → aba Integrações ───────────────────────────
    @step
    def _():
        w.optionsDialog.show()
        w.optionsDialog.tab_widget.setCurrentIndex(1)
        app.processEvents()
        grab(w.optionsDialog, '15_integrations_tab')
        w.optionsDialog.hide()

    # ── 16. Opções → aba Geral ─────────────────────────────────
    @step
    def _():
        w.optionsDialog.show()
        w.optionsDialog.tab_widget.setCurrentIndex(0)
        app.processEvents()
        grab(w.optionsDialog, '16_options_geral_tab')
        w.optionsDialog.hide()

    # ── Run all steps ──────────────────────────────────────────
    def run_steps():
        for i, fn in enumerate(steps, 1):
            print(f"Step {i}/{len(steps)}…")
            fn()
            app.processEvents()
        print(f"\nDone — {len(steps)} screenshots saved to: {OUT}/")
        app.quit()

    QTimer.singleShot(600, run_steps)
    app.exec()


if __name__ == '__main__':
    run()
