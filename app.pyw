import sys, os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Logging must be configured before any other local import
from _logging import setup_logging
setup_logging()

# Helpers
from _constants import *
from _settings import SettingsHelper
from _updater import UpdaterHelper
from _platforms import PlatformsHelper
from _tools import Tools, CacheGenerator

# Main class
from mainwindow import MainWindow

from theme import DARK_THEME



os.environ.setdefault('DEBUG', "0") # 0 = DISABLE
                                   # 1 = ERROR
                                   # 2 = WARNING
                                   # 3 = INFO
                                   # 4 = DEBUG



if __name__ == '__main__':
  # Initialize PyQt
  app = QApplication(sys.argv)

  # Load theme, icon (multi-resolution) and resources
  app.setStyleSheet(DARK_THEME)
  _icon = QIcon()
  for _size in (16, 32, 48, 64, 128, 256, 512):
      _icon.addPixmap(QPixmap(f"{ICONS_DIR}/icon_{_size}.png"))
  app.setWindowIcon(_icon)
  QResource.registerResource(RESOURCES_FILE)

  # Boot helpers
  settings = SettingsHelper()
  updater = UpdaterHelper()

  # Build catalogue cache if missing or expired
  if not os.path.exists(PLATFORMS_CACHE_DB) or not Tools.isCacheValid(settings.get('cache_expiration')):
      cache = CacheGenerator(app)
      cache.run()

  platforms = PlatformsHelper()

  # Initialize and show main window
  mainWindow = MainWindow(settings, updater, platforms)
  mainWindow.show()

  # Execute then shutdown
  sys.exit(app.exec())
