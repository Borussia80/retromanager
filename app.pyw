import sys, os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Logging must be configured before any other local import
from _logging import setup_logging
setup_logging()

# Helpers
from _constants import *
from _debug import *

# Main class
from splashscreen import SplashScreen
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

  # Show the splashscreen and do starting stuff
  splash = SplashScreen(app)
  splash.show()

  # Initialize main window
  mainWindow = MainWindow(splash.settings, splash.updater, splash.platforms)
  mainWindow.show()

  # Execute then shutdown
  sys.exit(app.exec())
