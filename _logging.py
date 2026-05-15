"""
Configures the Python logging infrastructure for retromanager.

Call setup_logging() once at startup (app.pyw) before any other import.
Afterwards every module can do:

    import logging
    log = logging.getLogger("retromanager.<module>")
    log.info("...")

Two rotating files are written to ~/.cache/retromanager/logs/:
  app.log    — INFO+ (max 5 MB × 3 backups)
  errors.log — ERROR+ (max 2 MB × 3 backups)
"""

import logging
import logging.handlers
import os

from _constants import CACHE_DIR

LOG_DIR = os.path.join(CACHE_DIR, "logs")
_FMT = "%(asctime)s  %(name)-24s  %(levelname)-8s  %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger("retromanager")
    if root.handlers:
        return root
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    app_h = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    app_h.setLevel(logging.INFO)
    app_h.setFormatter(formatter)

    err_h = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, "errors.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    err_h.setLevel(logging.ERROR)
    err_h.setFormatter(formatter)

    root.addHandler(app_h)
    root.addHandler(err_h)
    return root
