import sys
import os

# Startup timing — must be the very first local import
from _bootstrap import StartupTimer, start_memory_profiling, install_crash_hook
install_crash_hook()
StartupTimer.mark("_start")

from PyQt6.QtCore import QResource
from PyQt6.QtGui import QIcon, QPixmap, QPixmapCache
from PyQt6.QtWidgets import QApplication

# Logging before any other local import so every module gets handlers
from _logging import setup_logging
setup_logging()

from _constants import PLATFORMS_CACHE_DB, RESOURCES_FILE, ICONS_DIR
from _settings import SettingsHelper
from _updater import UpdaterHelper
from _platforms import PlatformsHelper
from _tools import Tools, CacheGenerator
from mainwindow import MainWindow
from theme import apply_theme

StartupTimer.mark("imports_done")

os.environ.setdefault("DEBUG", "0")  # 0=off  1=ERROR  2=WARNING  3=INFO  4=DEBUG


if __name__ == "__main__":
    if os.environ.get("DEBUG", "0") == "4":
        start_memory_profiling()

    app = QApplication(sys.argv)
    QPixmapCache.setCacheLimit(51_200)  # 50 MB thumbnail cache
    StartupTimer.mark("qapp_created")

    _icon = QIcon()
    for _size in (16, 32, 48, 64, 128, 256, 512):
        _icon.addPixmap(QPixmap(f"{ICONS_DIR}/icon_{_size}.png"))
    app.setWindowIcon(_icon)
    QResource.registerResource(RESOURCES_FILE)

    settings = SettingsHelper()
    updater = UpdaterHelper()
    StartupTimer.mark("settings_loaded")

    apply_theme(app, settings.get("theme"))

    if not os.path.exists(PLATFORMS_CACHE_DB) or not Tools.isCacheValid(settings.get("cache_expiration")):
        cache = CacheGenerator(app)
        cache.run()

    platforms = PlatformsHelper()
    StartupTimer.mark("platforms_loaded")

    mainWindow = MainWindow(settings, updater, platforms)
    StartupTimer.mark("mainwindow_created")
    StartupTimer.report()

    mainWindow.show()
    sys.exit(app.exec())
