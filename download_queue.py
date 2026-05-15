from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Helpers
from _platforms import PlatformsHelper

# Ui
from ui.ui_DownloadQueue import Ui_DownloadQueue



class CustomListItemWidget(QListWidgetItem):
  rom_platform = ""
  rom_name = ""
  rom_index = -1
  
  def __init__(self, platforms: PlatformsHelper, rom_platform: str, rom_index: int):
    super().__init__()
    self.rom_platform = rom_platform
    self.rom_name = platforms.getRomName(rom_platform, rom_index)
    self.rom_index = rom_index
    self.setText(f"[{self.rom_platform}] {self.rom_name}")



class DownloadQueue(QDialog, Ui_DownloadQueue):
  """This class handle the Download Queue"""
  def __init__(self, parent: QMainWindow, platforms: PlatformsHelper):
    super().__init__(parent)
    
    # Setup UI
    self.setupUi(self)
    self.pbDownload.setEnabled(False)
    self.pbDelete.setEnabled(False)
    self.pbDeleteAll.setEnabled(False)

    # Setup events
    self.lwToDownload.selectionChanged = self._onSelectionChanged
    self.pbDownload.clicked.connect(lambda: self.downloadClickedEvent())
    self.pbDelete.clicked.connect(self._onpbDeleteClicked)
    self.pbDeleteAll.clicked.connect(self._onpbDeleteAllClicked)

    # Setup variables
    self.platforms = platforms
    self.queue_dict = {}


  def show(self, *args) -> None:
    self._refreshList()
    return super().show()
  
  
  def add(self, platform_name: str, roms_indexes: list[int]) -> None:
    if platform_name not in self.queue_dict:
      self.queue_dict[platform_name] = []
    for rom_index in roms_indexes:
      if rom_index not in self.queue_dict[platform_name]:
        self.queue_dict[platform_name].append(rom_index)
    self.queue_dict[platform_name] = sorted(self.queue_dict[platform_name])
  

  def remove(self, platform_name: str, rom_index: int):
    if platform_name not in self.queue_dict or rom_index not in self.queue_dict[platform_name]:
      return
    self.queue_dict[platform_name].remove(rom_index)
    if len(self.queue_dict[platform_name]) == 0:
      del self.queue_dict[platform_name]
    self._refreshList()


  def items(self) -> list[tuple[str, int]]:
    queue_items = []
    for platform in self.queue_dict.keys():
      for rom_index in self.queue_dict[platform]:
        queue_items.append((platform, rom_index))
    return queue_items


  def getTotalCount(self) -> int:
    count = 0
    for i in self.queue_dict.keys():
      count += len(self.queue_dict[i])
    return count

  
  def updatedListEvent(self):
    # Do nothing. Overrided by the parent
    pass

  
  def downloadClickedEvent(self):
    # Do nothing. Overrided by the parent
    pass


  def _refreshList(self):
    self.lwToDownload.clear()
    for platform in self.queue_dict.keys():
      for rom_index in self.queue_dict[platform]:
        self.lwToDownload.addItem(CustomListItemWidget(self.platforms, platform, rom_index))
    if self.lwToDownload.count() > 0:
      self.pbDownload.setEnabled(True)
      self.pbDeleteAll.setEnabled(True)
    else:
      self.pbDownload.setEnabled(False)
      self.pbDeleteAll.setEnabled(False)
    self.updatedListEvent()


  def _onSelectionChanged(self, selected: QItemSelection, deselect: QItemSelection):
    try:
      text = self.lwToDownload.selectedItems()[0].text()
      self.pbDelete.setEnabled(True)
    except IndexError:
      self.pbDelete.setEnabled(False)


  def _onpbDeleteClicked(self, checked: bool):
    liw: CustomListItemWidget = self.lwToDownload.selectedItems()[0]
    self.queue_dict[liw.rom_platform].remove(liw.rom_index)
    self._refreshList()
  
  
  def _onpbDeleteAllClicked(self, checked: bool):
    if QMessageBox.warning(self, "Warning!", "Are you sure you want to delete the WHOLE QUEUE LIST ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
      self.queue_dict.clear()
      self._refreshList()
