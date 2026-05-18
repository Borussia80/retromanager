import json
import logging
import os

from PyQt6.QtCore import Qt, QItemSelection
from PyQt6.QtWidgets import QDialog, QListWidgetItem, QMainWindow, QMessageBox

_log = logging.getLogger("retromanager.download_queue")

# Ui
from ui.ui_DownloadQueue import Ui_DownloadQueue
from _constants import CACHE_DIR

_QUEUE_FILE = os.path.join(CACHE_DIR, "queue.json")



class CustomListItemWidget(QListWidgetItem):
  def __init__(self, rom_platform: str, rom_name: str):
    super().__init__()
    self.rom_platform = rom_platform
    self.rom_name = rom_name
    self.setText(f"[{self.rom_platform}] {self.rom_name}")



class DownloadQueue(QDialog, Ui_DownloadQueue):
  """Manages the download queue. Items are keyed by rom_name (string), not index."""

  def __init__(self, parent: QMainWindow):
    super().__init__(parent)

    # Setup UI
    self.setupUi(self)
    self.pbDownload.setEnabled(False)
    self.pbDelete.setEnabled(False)
    self.pbDeleteAll.setEnabled(False)

    # Setup events
    self.lwToDownload.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.pbDownload.clicked.connect(lambda: self.downloadClickedEvent())
    self.pbDelete.clicked.connect(self._onpbDeleteClicked)
    self.pbDeleteAll.clicked.connect(self._onpbDeleteAllClicked)

    self.queue_dict: dict[str, list[str]] = {}
    self._load()


  def show(self, *args) -> None:
    self._refreshList()
    return super().show()


  def add(self, platform_name: str, rom_names: list[str]) -> int:
    """Add rom_names to the queue for platform_name. Returns the number of newly added items."""
    if platform_name not in self.queue_dict:
      self.queue_dict[platform_name] = []
    added = 0
    for rom_name in rom_names:
      if rom_name not in self.queue_dict[platform_name]:
        self.queue_dict[platform_name].append(rom_name)
        added += 1
    self.queue_dict[platform_name] = sorted(self.queue_dict[platform_name])
    self._save()
    return added


  def remove(self, platform_name: str, rom_name: str):
    if platform_name not in self.queue_dict or rom_name not in self.queue_dict[platform_name]:
      return
    self.queue_dict[platform_name].remove(rom_name)
    if not self.queue_dict[platform_name]:
      del self.queue_dict[platform_name]
    self._save()
    self._refreshList()


  def items(self) -> list[tuple[str, str]]:
    """Return a snapshot of the queue as [(platform, rom_name), ...]."""
    return [
      (platform, rom_name)
      for platform, rom_names in self.queue_dict.items()
      for rom_name in rom_names
    ]


  def getTotalCount(self) -> int:
    return sum(len(names) for names in self.queue_dict.values())


  def updatedListEvent(self):
    pass


  def downloadClickedEvent(self):
    pass


  def _refreshList(self):
    self.lwToDownload.clear()
    for platform, rom_names in self.queue_dict.items():
      for rom_name in rom_names:
        self.lwToDownload.addItem(CustomListItemWidget(platform, rom_name))
    has_items = self.lwToDownload.count() > 0
    self.pbDownload.setEnabled(has_items)
    self.pbDeleteAll.setEnabled(has_items)
    self.pbDelete.setEnabled(False)
    self.updatedListEvent()


  def _onSelectionChanged(self, selected: QItemSelection, deselect: QItemSelection):
    self.pbDelete.setEnabled(bool(self.lwToDownload.selectedItems()))


  def _onpbDeleteClicked(self, checked: bool):
    item: CustomListItemWidget = self.lwToDownload.selectedItems()[0]
    self.remove(item.rom_platform, item.rom_name)


  def _save(self):
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
      with open(_QUEUE_FILE, "w") as f:
        json.dump(self.queue_dict, f)
    except OSError as e:
      _log.error("Failed to persist download queue to %s: %s", _QUEUE_FILE, e)

  def _load(self):
    try:
      with open(_QUEUE_FILE) as f:
        data = json.load(f)
      if isinstance(data, dict):
        self.queue_dict = {k: v for k, v in data.items() if isinstance(v, list)}
    except (FileNotFoundError, json.JSONDecodeError):
      pass

  def _onpbDeleteAllClicked(self, checked: bool):
    if QMessageBox.warning(self, "Atenção!", "Deseja remover TODOS os itens da fila?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
      self.queue_dict.clear()
      self._save()
      self._refreshList()
