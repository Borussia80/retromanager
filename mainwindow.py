from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from _settings import SettingsHelper
from _updater import UpdaterHelper
from _platforms import PlatformsHelper
from _tools import Tools, DownloadWorker
from _debug import *
from download_queue import DownloadQueue
from download_panel import DownloadQueuePanel
from platform_icons import PlatformItemWidget, GameTitleDelegate, FormatBadgeDelegate
from error_dialog import DownloadErrorDialog
from game_grid import GameGridWidget
from options import Options
from about import About


class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsHelper, updater: UpdaterHelper, platforms: PlatformsHelper):
        super().__init__()

        self.settings = settings
        self.updater = updater
        self.platforms = platforms
        self.optionsDialog = Options(self, settings)
        self.aboutDialog = About(self)
        self.download_queue = DownloadQueue(self)
        self.download_thread = None
        self.download_worker = None
        self.download_total_count = 0
        self.download_completed_count = 0
        self.download_failed = False
        self._active_rom_name = None
        self.table_placeholder_active = False

        self.filter_timer = QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.setInterval(150)
        self.filter_timer.timeout.connect(self._applyTableFilter)

        self._build_ui()
        self._build_menu()
        self._build_statusbar()
        self._connect_signals()

        self.setWindowTitle(f"retromanager {self.updater.currentVersionString()}")
        self.resize(1200, 680)

        self._checkUpdates(at_launch=True)
        self._loadPlatformsList()
        self._showEmptyTableMessage("Select a platform on the left to browse games.")

    # ──────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        root.addWidget(self._splitter)

        # ── Left: platform sidebar ──────────────────
        sidebar = QWidget()
        sidebar.setStyleSheet("background:#161b27;")
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(300)
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.setSpacing(0)

        sidebar_hdr = QWidget()
        sidebar_hdr.setFixedHeight(40)
        sidebar_hdr.setStyleSheet("background:#161b27;border-bottom:1px solid #2e3a52;")
        sidebar_hdr_lay = QHBoxLayout(sidebar_hdr)
        sidebar_hdr_lay.setContentsMargins(12, 0, 12, 0)
        lbl_platforms = QLabel("Platforms")
        lbl_platforms.setStyleSheet(
            "font-size:12px;font-weight:600;color:#a9b4cc;background:transparent;border:none;"
        )
        sidebar_hdr_lay.addWidget(lbl_platforms)
        sidebar_lay.addWidget(sidebar_hdr)

        self.lw_platforms = QListWidget()
        self.lw_platforms.setStyleSheet(
            "QListWidget { border:none; border-radius:0; background:#161b27; }"
            "QListWidget::item { padding:0; margin:0; }"
            "QListWidget::item:selected { background:#1e2d4a; }"
            "QListWidget::item:hover:!selected { background:#1e2535; }"
        )
        self.lw_platforms.setSpacing(0)
        sidebar_lay.addWidget(self.lw_platforms)

        self._splitter.addWidget(sidebar)

        # ── Middle: filter bar + game table ────────
        middle = QWidget()
        middle_lay = QVBoxLayout(middle)
        middle_lay.setContentsMargins(0, 0, 0, 0)
        middle_lay.setSpacing(0)

        # Filter bar
        filter_bar = QWidget()
        filter_bar.setFixedHeight(48)
        filter_bar.setStyleSheet("background:#0f1117;border-bottom:1px solid #2e3a52;")
        filter_lay = QHBoxLayout(filter_bar)
        filter_lay.setContentsMargins(12, 8, 12, 8)
        filter_lay.setSpacing(8)

        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText("Search by title, region, version, prototype, beta…")
        self.le_filter.setClearButtonEnabled(True)
        filter_lay.addWidget(self.le_filter)

        self.pb_eur = QPushButton("Europe")
        self.pb_usa = QPushButton("USA")
        self.pb_jpn = QPushButton("Japan")
        self.pb_all = QPushButton("All")
        for btn in (self.pb_eur, self.pb_usa, self.pb_jpn, self.pb_all):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            filter_lay.addWidget(btn)
        self.pb_all.setChecked(True)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color:#2e3a52;background:transparent;")
        filter_lay.addWidget(sep)

        # View toggle: List / Grid
        self.pb_view_list = QPushButton("≡")
        self.pb_view_grid = QPushButton("⊞")
        for btn in (self.pb_view_list, self.pb_view_grid):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedSize(28, 28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            filter_lay.addWidget(btn)
        self.pb_view_list.setChecked(True)
        self.pb_view_list.setToolTip("List view")
        self.pb_view_grid.setToolTip("Grid view")

        middle_lay.addWidget(filter_bar)

        # Table
        self.tw_romsList = QTableWidget()
        self.tw_romsList.setColumnCount(6)
        self.tw_romsList.setRowCount(0)
        self.tw_romsList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_romsList.setAlternatingRowColors(False)
        self.tw_romsList.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_romsList.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tw_romsList.setMouseTracking(True)
        self.tw_romsList.verticalHeader().setVisible(False)
        self.tw_romsList.horizontalHeader().setStretchLastSection(False)
        self.tw_romsList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tw_romsList.setShowGrid(False)
        self.tw_romsList.verticalHeader().setDefaultSectionSize(28)

        headers = ["Game", "Size", "File", "MD5", "CRC32", "SHA1"]
        for i, h in enumerate(headers):
            self.tw_romsList.setHorizontalHeaderItem(i, QTableWidgetItem(h))

        hh = self.tw_romsList.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tw_romsList.setColumnWidth(2, 48)

        self._toggleTechnicalColumns(False)

        # Game title delegate for badges
        self._title_delegate = GameTitleDelegate(self.tw_romsList)
        self.tw_romsList.setItemDelegateForColumn(0, self._title_delegate)

        self._format_delegate = FormatBadgeDelegate(self.tw_romsList)
        self.tw_romsList.setItemDelegateForColumn(2, self._format_delegate)

        # Grid view
        self.game_grid = GameGridWidget()

        # Stacked view (List = 0, Grid = 1)
        self._view_stack = QStackedWidget()
        self._view_stack.addWidget(self.tw_romsList)
        self._view_stack.addWidget(self.game_grid)
        middle_lay.addWidget(self._view_stack)

        self._splitter.addWidget(middle)

        # ── Right: download panel ────────────────
        self.download_panel = DownloadQueuePanel()
        self._splitter.addWidget(self.download_panel)

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        self._splitter.setSizes([230, 750, 230])

    def _build_menu(self):
        menubar = self.menuBar()

        menu_options = menubar.addMenu("Options")
        self.actionToggleTechnical = QAction("Show technical columns", self)
        self.actionToggleTechnical.setCheckable(True)
        self.actionToggleTechnical.triggered.connect(self._toggleTechnicalColumns)
        menu_options.addAction(self.actionToggleTechnical)
        menu_options.addSeparator()
        act_settings = QAction("Settings", self)
        act_settings.setShortcut("F2")
        act_settings.triggered.connect(self.optionsDialog.show)
        menu_options.addAction(act_settings)
        menu_options.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        menu_options.addAction(act_exit)

        menu_help = menubar.addMenu("Help")
        act_updates = QAction("Check for updates…", self)
        act_updates.triggered.connect(self._checkUpdates)
        menu_help.addAction(act_updates)
        menu_help.addSeparator()
        act_about = QAction("About…", self)
        act_about.triggered.connect(self.aboutDialog.show)
        menu_help.addAction(act_about)
        act_about_qt = QAction("About Qt…", self)
        act_about_qt.triggered.connect(lambda: QMessageBox.aboutQt(self, "About Qt…"))
        menu_help.addAction(act_about_qt)

    def _build_statusbar(self):
        self.statusbar_catalog = QLabel()
        self.statusBar().addWidget(self.statusbar_catalog)

        self.statusbar_queue = QLabel()
        self.statusbar_queue.setMinimumWidth(160)
        self.statusbar_queue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.statusbar_queue.mousePressEvent = self.download_queue.show
        self.statusBar().addWidget(self.statusbar_queue)

        self.statusbar_update = QLabel()
        self.statusBar().addPermanentWidget(self.statusbar_update)

    def _connect_signals(self):
        self.lw_platforms.itemClicked.connect(self._onListwidgetSelectionChanged)
        self.tw_romsList.customContextMenuRequested.connect(self._onRomslistRightClick)
        self.tw_romsList.itemDoubleClicked.connect(self._downloadNowContextMenu)
        self.le_filter.textChanged.connect(self._filterTableWidget)
        self.download_panel.downloadRequested.connect(self._launchRomsDownload)
        self.pb_view_list.toggled.connect(lambda on: self._switch_view("list") if on else None)
        self.pb_view_grid.toggled.connect(lambda on: self._switch_view("grid") if on else None)
        self.game_grid.romDoubleClicked.connect(self._downloadRomByName)
        self.pb_eur.toggled.connect(self._filterTableWidget)
        self.pb_usa.toggled.connect(self._filterTableWidget)
        self.pb_jpn.toggled.connect(self._filterTableWidget)
        self.pb_all.toggled.connect(self._filterTableWidget)
        self.download_queue.updatedListEvent = self._updateStatusbarQueueText
        self.download_queue.downloadClickedEvent = self._launchRomsDownload

    # ──────────────────────────────────────────────
    # Platform list
    # ──────────────────────────────────────────────

    def _loadPlatformsList(self):
        available = 0
        total = 0
        for name in self.platforms.getPlatforms():
            count = self.platforms.getRomsCount(name)
            total += count
            if count > 0:
                available += 1
            item = QListWidgetItem(self.lw_platforms)
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setSizeHint(QSize(0, 52))
            if count == 0:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            widget = PlatformItemWidget(name, count)
            self.lw_platforms.setItemWidget(item, widget)

        self.statusbar_catalog.setText(
            f"{available}/{self.platforms.platformsCount()} platforms  ·  {total:,} items"
        )

    # ──────────────────────────────────────────────
    # Game table
    # ──────────────────────────────────────────────

    def _toggleTechnicalColumns(self, checked: bool = False):
        for col in [3, 4, 5]:
            self.tw_romsList.setColumnHidden(col, not checked)

    def _onListwidgetSelectionChanged(self, item: QListWidgetItem):
        platform_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
        self.table_placeholder_active = False
        self.tw_romsList.setSortingEnabled(False)
        self.tw_romsList.setRowCount(0)

        rom_names = []
        for i, (rom_name, rom_data) in enumerate(self.platforms.getRoms(platform_name)):
            rom_names.append(rom_name)
            rom_name_item = QTableWidgetItem(rom_name)
            rom_name_item.setToolTip(self._buildRomSummary(platform_name, rom_name, rom_data))

            rom_size_item = QTableWidgetItem(Tools.convertSizeToReadable(rom_data['size']))
            rom_size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            rom_format_item = QTableWidgetItem(rom_data['format'].upper())
            rom_format_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rom_format_item.setForeground(QColor("#6b7a99"))

            rom_md5_item  = QTableWidgetItem(rom_data['md5'])
            rom_crc32_item = QTableWidgetItem(rom_data['crc32'].upper())
            rom_sha1_item = QTableWidgetItem(rom_data['sha1'])
            for it in (rom_md5_item, rom_crc32_item, rom_sha1_item):
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor("#6b7a99"))

            self.tw_romsList.insertRow(i)
            self.tw_romsList.setItem(i, 0, rom_name_item)
            self.tw_romsList.setItem(i, 1, rom_size_item)
            self.tw_romsList.setItem(i, 2, rom_format_item)
            self.tw_romsList.setItem(i, 3, rom_md5_item)
            self.tw_romsList.setItem(i, 4, rom_crc32_item)
            self.tw_romsList.setItem(i, 5, rom_sha1_item)

        self.tw_romsList.setSortingEnabled(True)
        self.tw_romsList.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._applyTableFilter()

        # Populate grid with sorted names
        self.game_grid.load(platform_name, sorted(rom_names))

        self.statusBar().showMessage(
            f"{platform_name}: {len(rom_names):,} items", 5000
        )

    def _showEmptyTableMessage(self, message: str):
        self.table_placeholder_active = True
        self.tw_romsList.setRowCount(1)
        self.tw_romsList.setSpan(0, 0, 1, self.tw_romsList.columnCount())
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(QColor("#3d4f6e"))
        self.tw_romsList.setItem(0, 0, item)

    def _filterTableWidget(self):
        self.filter_timer.start()

    def _applyTableFilter(self):
        if self.table_placeholder_active:
            return
        keywords = self.le_filter.text().strip().lower().split()
        region = self._selectedRegion()
        visible = 0
        for i in range(self.tw_romsList.rowCount()):
            name = self.tw_romsList.item(i, 0).text()
            show = self._romMatchesFilters(name, keywords, region)
            self.tw_romsList.setRowHidden(i, not show)
            if show:
                visible += 1
        self.game_grid.apply_filter(keywords, region)
        self.statusBar().showMessage(f"{visible:,} visible item(s)", 3000)

    def _selectedRegion(self):
        if self.pb_eur.isChecked(): return "Europe"
        if self.pb_usa.isChecked(): return "USA"
        if self.pb_jpn.isChecked(): return "Japan"
        return None

    def _romMatchesFilters(self, rom_name: str, keywords: list[str], region: str | None) -> bool:
        target = rom_name.lower()
        if region and f"({region})".lower() not in target:
            return False
        return all(kw in target for kw in keywords)

    def _buildRomSummary(self, platform_name: str, rom_name: str, rom_data: dict) -> str:
        import re
        tags = re.findall(r'\(([^)]+)\)', rom_name)
        tags_text = ", ".join(tags) if tags else "—"
        return (
            f"{rom_name}\n"
            f"Platform: {platform_name}\n"
            f"Tags: {tags_text}\n"
            f"Size: {Tools.convertSizeToReadable(rom_data['size'])}\n"
            f"Format: {rom_data['format']}"
        )

    def _selectedRomContext(self):
        selected = self.tw_romsList.selectionModel().selectedRows()
        if not selected or not self.lw_platforms.selectedItems():
            return None
        row = selected[0].row()
        platform = self.lw_platforms.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        rom_name = self.tw_romsList.item(row, 0).text()
        return platform, rom_name, self.platforms.getRom(platform, rom_name)

    def _showSelectedRomDetails(self, *args):
        ctx = self._selectedRomContext()
        if not ctx:
            return
        platform, rom_name, rom_data = ctx
        details = (
            f"<b>{rom_name}</b><br><br>"
            f"<b>Platform:</b> {platform}<br>"
            f"<b>Size:</b> {Tools.convertSizeToReadable(rom_data['size'])}<br>"
            f"<b>Format:</b> {rom_data['format']}<br><br>"
            f"<b>MD5:</b> {rom_data['md5']}<br>"
            f"<b>CRC32:</b> {rom_data['crc32'].upper()}<br>"
            f"<b>SHA1:</b> {rom_data['sha1']}"
        )
        QMessageBox.information(self, "Game details", details)

    def _onRomslistRightClick(self, point: QPoint):
        if self.table_placeholder_active:
            return
        menu = QMenu(self.tw_romsList)
        has_sel = bool(self.tw_romsList.selectionModel().selectedRows())

        act_queue = QAction("Add to Queue", self)
        act_queue.setEnabled(has_sel)
        act_queue.triggered.connect(self._addToQueue)

        act_now = QAction("Download Now", self)
        act_now.setEnabled(has_sel)
        act_now.triggered.connect(self._downloadNowContextMenu)

        act_details = QAction("View Details", self)
        act_details.setEnabled(has_sel)
        act_details.triggered.connect(self._showSelectedRomDetails)

        menu.addAction(act_queue)
        menu.addAction(act_now)
        menu.addSeparator()
        menu.addAction(act_details)
        menu.exec(QCursor.pos())

    # ──────────────────────────────────────────────
    # View switching
    # ──────────────────────────────────────────────

    def _switch_view(self, mode: str):
        self._view_stack.setCurrentIndex(0 if mode == "list" else 1)

    # ──────────────────────────────────────────────
    # Queue management
    # ──────────────────────────────────────────────

    def _downloadRomByName(self, rom_name: str):
        """Called from grid card double-click."""
        if not self.lw_platforms.selectedItems():
            return
        platform = self.lw_platforms.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        self.download_queue.add(platform, [rom_name])
        self._updateStatusbarQueueText()
        self._launchRomsDownload()

    def _addToQueue(self):
        if not self.lw_platforms.selectedItems():
            return
        platform = self.lw_platforms.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        selected_names = [
            self.tw_romsList.item(row.row(), 0).text()
            for row in self.tw_romsList.selectedIndexes()
            if row.column() == 0 and not self.tw_romsList.isRowHidden(row.row())
        ]
        added = self.download_queue.add(platform, selected_names)
        self._updateStatusbarQueueText()
        self.statusBar().showMessage(f"{added} item(s) added to queue", 3000)

    def _downloadNowContextMenu(self):
        self._addToQueue()
        self._launchRomsDownload()

    def _updateStatusbarQueueText(self):
        count = self.download_queue.getTotalCount()
        is_running = bool(self.download_thread and self.download_thread.isRunning())
        if count > 0:
            self.statusbar_queue.setText(f"<a href='#'>{count} item(s) in queue</a>")
        else:
            self.statusbar_queue.setText("")
        self.download_panel.set_downloading(is_running)
        self.download_panel._btn_start.setEnabled(count > 0 and not is_running)

    # ──────────────────────────────────────────────
    # Download
    # ──────────────────────────────────────────────

    def _launchRomsDownload(self):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.information(self, "Download in progress", "A download is already running.")
            return
        if self.download_queue.getTotalCount() == 0:
            QMessageBox.information(self, "Download queue", "No items are queued for download.")
            return

        items = self.download_queue.items()
        self.download_total_count = len(items)
        self.download_completed_count = 0
        self.download_failed = False
        self._active_rom_name = None

        # Pre-populate panel with all queued items
        self.download_panel.clear()
        for _, rom_name in items:
            self.download_panel.add_item(rom_name)
        self.download_panel.set_downloading(True)
        self.download_panel._btn_start.setEnabled(False)

        self.download_thread = QThread(self)
        self.download_worker = DownloadWorker(self.settings, self.platforms, items)
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.startedItem.connect(self._onDownloadStartedItem)
        self.download_worker.progress.connect(self._onDownloadProgress)
        self.download_worker.completedItem.connect(self._onDownloadCompletedItem)
        self.download_worker.failedItem.connect(self._onDownloadFailedItem)
        self.download_worker.cancelled.connect(self._onDownloadCancelled)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self._onDownloadThreadFinished)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def _onDownloadStartedItem(self, platform: str, rom_name: str, current: int, total: int):
        self._active_rom_name = rom_name
        self.download_panel.start_item(rom_name)
        self.statusBar().showMessage(
            f"Downloading {current}/{total}: [{platform}] {rom_name}"
        )

    def _onDownloadProgress(self, bytes_done: int, total_bytes: int, speed: float):
        if self._active_rom_name:
            self.download_panel.update_progress(self._active_rom_name, bytes_done, total_bytes, speed)

    def _onDownloadCompletedItem(self, platform: str, rom_name: str):
        self.download_completed_count += 1
        self.download_queue.remove(platform, rom_name)
        self.download_panel.complete_item(rom_name)
        self._updateStatusbarQueueText()

    def _onDownloadFailedItem(self, platform: str, rom_name: str, error: str):
        self.download_failed = True
        self.download_panel.fail_item(rom_name, error)
        DebugHelper.print(DebugType.TYPE_ERROR, f"Download failed [{platform}] {rom_name}: {error}", "downloader")
        dlg = DownloadErrorDialog(rom_name, platform, error, parent=self)
        if dlg.exec() == DownloadErrorDialog.DialogCode.Accepted:
            QTimer.singleShot(0, self._launchRomsDownload)

    def _onDownloadCancelled(self):
        self.download_failed = True
        if self._active_rom_name:
            self.download_panel.cancel_item(self._active_rom_name)

    def _onDownloadThreadFinished(self):
        self.download_thread = None
        self.download_worker = None
        self._active_rom_name = None
        self._updateStatusbarQueueText()
        if not self.download_failed:
            self.statusBar().showMessage(
                f"Downloaded {self.download_completed_count} item(s).", 5000
            )

    def _cancelDownload(self):
        if self.download_worker:
            self.download_worker.cancel()

    # ──────────────────────────────────────────────
    # Updates
    # ──────────────────────────────────────────────

    def _checkUpdates(self, at_launch: bool = False):
        def ask():
            ans = QMessageBox.question(
                self, "Update available",
                f"An update is available!\n\n"
                f"Current: {self.updater.currentVersionString()}\n"
                f"Latest:  {self.updater.lastestVersionString()}\n\n"
                "Would you like to update now?"
            )
            if ans == QMessageBox.StandardButton.Yes:
                QMessageBox.warning(self, "Updating…", "Not yet implemented, sorry.")
            else:
                self.statusbar_update.setText("New version available!")

        update_available = self.updater.updateAvailable() if self.settings.get('check_updates') else False

        if at_launch and self.settings.get('check_updates') and update_available:
            ask()
        elif at_launch and self.settings.get('check_updates') and not update_available:
            self.statusbar_update.setText("Up to date.")
        elif not at_launch and update_available:
            ask()
        elif not at_launch and not update_available:
            QMessageBox.information(self, "Update", "You are up to date.")
            self.statusbar_update.setText("Up to date.")
