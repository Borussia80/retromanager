from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Ui
from ui.ui_Options import Ui_Dialog as Ui

# Helpers
from _settings import SettingsHelper


_CACHE_PRESETS = [
    ("A cada 30 dias (recomendado)", 30),
    ("A cada 7 dias",                 7),
    ("A cada 90 dias",               90),
    ("A cada inicialização",          1),
    ("Nunca (modo offline)",         -1),
]


class Options(QDialog, Ui):
  _settings: SettingsHelper

  def __init__(self, parent, settings: SettingsHelper):
    super().__init__(parent)
    self._settings = settings

    # Setup UI
    self.setupUi(self)
    self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)

    # Populate cache presets with userData so labels can change without breaking saves
    for label, days in _CACHE_PRESETS:
        self.cb_cache_expiration.addItem(label, days)

    self.le_DownloadPath.setAcceptDrops(True)

    # Setup events
    self.pb_BrowsePath.clicked.connect(self._onBrowsePathClicked)
    self.accepted.connect(self._onAccept)
  

  def show(self) -> None:
    # Cache expiration — find by userData (days value), default to first preset
    days = self._settings.get('cache_expiration')
    idx = self.cb_cache_expiration.findData(days)
    self.cb_cache_expiration.setCurrentIndex(idx if idx >= 0 else 0)

    # Download path
    self.le_DownloadPath.setText(self._settings.get('download_path'))
    
    # Decompress after download
    self.cb_unzip.setChecked(self._settings.get('unzip'))
    
    # Check for updates at startup
    self.cb_checkupdates.setChecked(self._settings.get('check_updates'))
    return super().show()


  def _onBrowsePathClicked(self):
    new_path = QFileDialog.getExistingDirectory()
    if new_path != "": self.le_DownloadPath.setText(new_path)


  def _onAccept(self):
    import os

    # Cache expiration — read days value from userData, not display text
    days = self.cb_cache_expiration.currentData()
    if days is not None:
        self._settings.update(['cache_expiration', days])

    # Download path
    if os.path.isdir(self.le_DownloadPath.text()):
      self._settings.update(['download_path', self.le_DownloadPath.text()])

    # Decompress after download
    self._settings.update(['unzip', self.cb_unzip.isChecked()])

    # Check for updates at startup
    self._settings.update(['check_updates', self.cb_checkupdates.isChecked()])
    
    # Write settings
    self._settings.write()
