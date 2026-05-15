from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Helpers
from _settings import SettingsHelper
from _updater import UpdaterHelper
from _platforms import PlatformsHelper
from _tools import Tools, RomDownload, Unzip
from _debug import *

# Ui
from ui.ui_MainWindow import Ui_MainWindow as Ui
from ui.ui_DownloadPane import Ui_DownloadPane

# Dialogs
from download_queue import DownloadQueue
from options import Options
from about import About



class DownloadPane(QWidget, Ui_DownloadPane):
  """This class made the jonction between the «Download_Pane.ui» and the main window."""
  def __init__(self, gb_parent: QGroupBox):
    super().__init__(gb_parent)
    self.setupUi(self)
    self.parent_gb_layout = QVBoxLayout()
    self.parent_gb_layout.addWidget(self)
    self.hide()



class MainWindow(QMainWindow, Ui):
  """This is the main window class."""
  def __init__(self, settings: SettingsHelper, updater: UpdaterHelper, platforms: PlatformsHelper):
    super().__init__()
    self.setupUi(self)

    # Setup local variables
    self.settings = settings
    self.updater = updater
    self.platforms = platforms
    self.optionsDialog = Options(self, settings)
    self.aboutDialog = About(self)
    self.download_pane = DownloadPane(self.gb_downloads)
    self.download_queue = DownloadQueue(self, self.platforms)

    # Setup form
    self.setWindowTitle(f"retromanager {self.updater.currentVersionString()}")
    self.le_filter.setPlaceholderText("Search games by title, region, version, prototype, beta...")
    self.gb_regions.setTitle("Region")
    self.pb_eur.setText("Europe")
    self.pb_usa.setText("USA")
    self.pb_jpn.setText("Japan")
    self.pb_all.setText("All")
    self.pb_eur.setToolTip("Show Europe releases")
    self.pb_usa.setToolTip("Show USA releases")
    self.pb_jpn.setToolTip("Show Japan releases")
    self.pb_all.setToolTip("Show every region")
    self.gb_downloads.setTitle("Download queue")
    self.tw_romsList.setColumnWidth(0, int(self.tw_romsList.width() / 2.42))
    self.tw_romsList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.tw_romsList.itemDoubleClicked.connect(self._showSelectedRomDetails)
    self._setupTableHeaders()
    self.gb_downloads.setLayout(self.download_pane.parent_gb_layout)

    # Setup statusbar
    self.statusbar_catalog = QLabel()
    self.statusbar.addWidget(self.statusbar_catalog)
    self.statusbar_update = QLabel()
    self.statusbar.addPermanentWidget(self.statusbar_update)
    self.statusbar_queue = QLabel()
    self.statusbar_queue.setMinimumWidth(150)
    self.statusbar_queue.mousePressEvent = self.download_queue.show
    self.statusbar.addWidget(self.statusbar_queue)
    
    # Setup download queue
    self.download_queue.updatedListEvent = self._updateStatusbarQueueText
    self.download_queue.downloadClickedEvent = self._launchRomsDownload

    # Setup menu events
    self.actionShowOptions.triggered.connect(lambda: self.optionsDialog.show())
    self.actionExit.triggered.connect(lambda: self.close())
    self.actionGet_help.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/silverlays/NoIntro-Roms-Downloader/wiki')))
    self.actionCheck_for_updates.triggered.connect(lambda: self._checkUpdates())
    self.actionAbout.triggered.connect(self.aboutDialog.show)
    self.actionAbout_Qt.triggered.connect(lambda: QMessageBox.aboutQt(self, 'About Qt...'))
    self.actionToggleTechnical = QAction("Show technical columns", self)
    self.actionToggleTechnical.setCheckable(True)
    self.actionToggleTechnical.triggered.connect(self._toggleTechnicalColumns)
    self.menuOptions.insertAction(self.actionShowOptions, self.actionToggleTechnical)
    
    # Setup other events
    self.lw_platforms.itemClicked.connect(self._onListwidgetSelectionChanged)
    self.tw_romsList.customContextMenuRequested.connect(self._onRomslistRightClick)
    self.le_filter.textChanged.connect(self._filterTableWidget)
    self.pb_eur.toggled.connect(self._filterTableWidget)
    self.pb_usa.toggled.connect(self._filterTableWidget)
    self.pb_jpn.toggled.connect(self._filterTableWidget)
    self.pb_all.toggled.connect(self._filterTableWidget)
    self.gb_downloads.clicked.connect(self._onDownloadPaneClicked)

    # Startup task(s)
    self._checkUpdates(at_launch=True)
    self._loadPlatformsList()


  def _setupTableHeaders(self):
    self.tw_romsList.horizontalHeaderItem(0).setText("Game")
    self.tw_romsList.horizontalHeaderItem(1).setText("Size")
    self.tw_romsList.horizontalHeaderItem(2).setText("File")
    self.tw_romsList.horizontalHeaderItem(3).setText("MD5")
    self.tw_romsList.horizontalHeaderItem(4).setText("CRC32")
    self.tw_romsList.horizontalHeaderItem(5).setText("SHA1")
    self._toggleTechnicalColumns(False)


  def _toggleTechnicalColumns(self, checked: bool):
    for column in [3, 4, 5]:
      self.tw_romsList.setColumnHidden(column, not checked)


  def _checkUpdates(self, at_launch: bool = False):
    """Check for software update.

    Args:
        at_launch (bool, optional): 'True' if the application just started. Defaults to False.
    """
    def Ask():
      answer = QMessageBox.question(self, "Update available", f"An update is available!\n\nActual version: {self.updater.currentVersionString()}\nLastest version: {self.updater.lastestVersionString()}\n\nWould you like to update now ?")
      if answer == QMessageBox.StandardButton.Yes:
        QMessageBox.warning(self, 'Updating...', 'Not yet implemented, sorry.')
        ###
        ### TODO: IMPLEMENT SOFTWARE UPDATE
        ###
      else:
        self.statusbar_update.setText("New version available!")

    update_available = self.updater.updateAvailable() if self.settings.get('check_updates') else False
    
    if at_launch and self.settings.get('check_updates') and update_available: Ask()
    elif at_launch and self.settings.get('check_updates') and not update_available: self.statusbar_update.setText("You are up-to-date.")
    elif not at_launch and update_available: Ask()
    elif not at_launch and not update_available:
      QMessageBox.information(self, "Update", "You are up-to-date.")
      self.statusbar_update.setText("You are up-to-date.")


  def _loadPlatformsList(self):
    available_platforms = 0
    total_roms = 0

    for i in range(self.platforms.platformsCount()):
      name = self.platforms.getPlatformName(i)
      rom_count = self.platforms.getRomsCount(name)
      total_roms += rom_count
      item_text = f"{name} ({rom_count})"
      if rom_count == 0:
        item_text = f"{name} - Unavailable"
      else:
        available_platforms += 1

      item = QListWidgetItem(QIcon(':/app.ico'), item_text)
      item.setData(Qt.ItemDataRole.UserRole, name)
      if rom_count == 0:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        item.setForeground(QBrush(Qt.GlobalColor.gray))
        item.setToolTip("The current catalogue source did not return files for this platform.")
      self.lw_platforms.addItem(item)

    self.statusbar_catalog.setText(f"{available_platforms}/{self.platforms.platformsCount()} platforms available - {total_roms} items")


  def _filterTableWidget(self):
    """Handle table filtering."""
    keywords = self.le_filter.text().strip().lower().split()
    region = self._selectedRegion()

    for i in range(self.tw_romsList.rowCount()):
      rom_name = self.tw_romsList.item(i, 0).text()
      self.tw_romsList.setRowHidden(i, not self._romMatchesFilters(rom_name, keywords, region))

    visible_count = sum(0 if self.tw_romsList.isRowHidden(i) else 1 for i in range(self.tw_romsList.rowCount()))
    self.statusbar.showMessage(f"{visible_count} visible item(s)", 3000)


  def _selectedRegion(self):
    if self.pb_eur.isChecked(): return "Europe"
    if self.pb_usa.isChecked(): return "USA"
    if self.pb_jpn.isChecked(): return "Japan"
    return None


  def _romMatchesFilters(self, rom_name: str, keywords: list[str], region: str | None) -> bool:
    search_target = rom_name.lower()
    if region and f"({region})".lower() not in search_target:
      return False
    return all(keyword in search_target for keyword in keywords)


  def _updateStatusbarQueueText(self):
    count = self.download_queue.getTotalCount()
    self.statusbar_queue.setText(f"<a href='#'>{count} item(s) in queue</a>") if count > 0 else self.statusbar_queue.setText("")


  def _addToQueue(self):
    self.download_queue.add(self.platforms.getPlatformName(self.lw_platforms.selectedIndexes()[0].row()), [row.row() for row in self.tw_romsList.selectedIndexes() if row.column() == 0])
    self._updateStatusbarQueueText()
  

  def _downloadNowContextMenu(self):
    self._addToQueue()
    self._launchRomsDownload()


  def _launchRomsDownload(self):
    DebugHelper.print(DebugType.TYPE_INFO, "Download started...")
    if self.download_queue.getTotalCount() == 0:
      QMessageBox.information(self, "Download queue", "No items are queued for download.")
      return

    self.gb_downloads.setChecked(True)
    self.download_pane.show()
    total_count = self.download_queue.getTotalCount()
    completed_count = 0
    self.download_pane.pb_progress.setMaximum(total_count)
    self.download_pane.pb_progress.setValue(0)
    for platform in self.download_queue.queue_dict:
      for i in range(len(self.download_queue.queue_dict[platform])):
        rom_name = self.platforms.getRomName(platform, self.download_queue.queue_dict[platform][0])
        rom_index = self.download_queue.queue_dict[platform][0]
        self.download_pane.l_job.setText(f"[{platform}] {rom_name}")
        self.download_pane.l_progress.setText(f"{completed_count}/{total_count}")
        self.repaint()
        try:
          RomDownload(self.settings, self.platforms, platform, rom_index)
          if self.settings.get('unzip'): Unzip(self.settings, f"{rom_name}.{self.platforms.getRom(platform, rom_name)['format']}")
          self.download_queue.remove(platform, rom_index)
          completed_count += 1
        except Exception as e:
          DebugHelper.print(DebugType.TYPE_ERROR, f"Download failed for [{platform}] {rom_name}: {e}", "downloader")
          QMessageBox.warning(
            self,
            "Download failed",
            f"Could not download:\n\n[{platform}] {rom_name}\n\n{e}\n\nThe item was left in the queue so you can try again."
          )
          self.download_pane.l_job.setText("Download failed")
          self.download_pane.l_progress.setText(f"{completed_count}/{total_count}")
          return
        self.download_pane.pb_progress.setValue(completed_count)
        self.repaint()
    self.download_pane.l_job.setText("N/A")
    self.download_pane.l_progress.setText(f"{completed_count}/{total_count}")
    QMessageBox.information(self, "Downloads complete", f"Downloaded {completed_count} item(s).")


  def _onListwidgetSelectionChanged(self, item: QListWidgetItem):
    platform_name = item.data(Qt.ItemDataRole.UserRole) or item.text()

    # Clear the table
    self.tw_romsList.setRowCount(0)

    # Fill the table with new content
    for i in range(self.platforms.getRomsCount(platform_name)):
      rom_name = self.platforms.getRomName(platform_name, i)
      rom_data = self.platforms.getRom(platform_name, rom_name)

      # Creating Items for table's row
      rom_name_item = QTableWidgetItem(rom_name)
      rom_name_item.setToolTip(self._buildRomSummary(platform_name, rom_name, rom_data))
      rom_size_item = QTableWidgetItem(Tools.convertSizeToReadable(rom_data['size']))
      rom_size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      rom_format_item = QTableWidgetItem(rom_data['format'])
      rom_format_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      rom_md5_item = QTableWidgetItem(rom_data['md5'])
      rom_md5_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      rom_crc32_item = QTableWidgetItem(rom_data['crc32'].upper())
      rom_crc32_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      rom_sha1_item = QTableWidgetItem(rom_data['sha1'])
      rom_sha1_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      
      self.tw_romsList.insertRow(i)
      self.tw_romsList.setItem(i, 0, rom_name_item)
      self.tw_romsList.setItem(i, 1, rom_size_item)
      self.tw_romsList.setItem(i, 2, rom_format_item)
      self.tw_romsList.setItem(i, 3, rom_md5_item)
      self.tw_romsList.setItem(i, 4, rom_crc32_item)
      self.tw_romsList.setItem(i, 5, rom_sha1_item)
    
    # Resize columns and sort
    self.tw_romsList.resizeColumnsToContents()
    self.tw_romsList.horizontalHeader().setStretchLastSection(False)
    self.tw_romsList.setColumnWidth(0, max(360, self.tw_romsList.columnWidth(0)))
    #self.tw_romsList.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    # Apply any previous filters
    self._filterTableWidget()
    self.statusbar.showMessage(f"{platform_name}: {self.platforms.getRomsCount(platform_name)} item(s)", 5000)


  def _buildRomSummary(self, platform_name: str, rom_name: str, rom_data: dict) -> str:
    tags = self._extractReleaseTags(rom_name)
    tags_text = ", ".join(tags) if tags else "No release tags found"
    return (
      f"{rom_name}\n"
      f"Platform: {platform_name}\n"
      f"Tags: {tags_text}\n"
      f"Size: {Tools.convertSizeToReadable(rom_data['size'])}\n"
      f"File: {rom_data['format']}"
    )


  def _extractReleaseTags(self, rom_name: str) -> list[str]:
    tags = []
    current = ""
    inside = False
    for char in rom_name:
      if char == "(":
        inside = True
        current = ""
      elif char == ")" and inside:
        inside = False
        if current:
          tags.append(current)
      elif inside:
        current += char
    return tags


  def _selectedRomContext(self):
    selected_rows = self.tw_romsList.selectionModel().selectedRows()
    if not selected_rows or not self.lw_platforms.selectedItems():
      return None
    row = selected_rows[0].row()
    platform_name = self.lw_platforms.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
    rom_name = self.tw_romsList.item(row, 0).text()
    return platform_name, rom_name, self.platforms.getRom(platform_name, rom_name)


  def _showSelectedRomDetails(self, *args):
    context = self._selectedRomContext()
    if not context:
      return

    platform_name, rom_name, rom_data = context
    details = (
      f"<b>{rom_name}</b><br><br>"
      f"<b>Platform:</b> {platform_name}<br>"
      f"<b>Size:</b> {Tools.convertSizeToReadable(rom_data['size'])}<br>"
      f"<b>File:</b> {rom_data['format']}<br><br>"
      f"<b>MD5:</b> {rom_data['md5']}<br>"
      f"<b>CRC32:</b> {rom_data['crc32'].upper()}<br>"
      f"<b>SHA1:</b> {rom_data['sha1']}"
    )
    QMessageBox.information(self, "Game details", details)


  def _onDownloadPaneClicked(self):
    if self.gb_downloads.isChecked():
      self.download_pane.show()
      self.gb_downloads.setFixedHeight(100)
    else:
      self.download_pane.hide()
      self.gb_downloads.setFixedHeight(20)


  def _onRomslistRightClick(self, point: QPoint):
    menu = QMenu(self.tw_romsList)
    has_selection = bool(self.tw_romsList.selectionModel().selectedRows())
    
    add_to_queue = QAction("Add to Queue")
    add_to_queue.setEnabled(has_selection)
    add_to_queue.triggered.connect(lambda: self._addToQueue())

    download_now = QAction("Download Now")
    download_now.setEnabled(has_selection)
    download_now.triggered.connect(lambda: self._downloadNowContextMenu())

    details = QAction("View Details")
    details.setEnabled(has_selection)
    details.triggered.connect(self._showSelectedRomDetails)
    
    menu.exec([add_to_queue, download_now, details], QCursor.pos(), parent=self.tw_romsList)
