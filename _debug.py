import logging
import os
from enum import Enum
from typing import Literal

from PyQt6.QtCore import qDebug

_log = logging.getLogger("retromanager")

_PY_LEVEL = {
    "TYPE_INFO":    logging.INFO,
    "TYPE_WARNING": logging.WARNING,
    "TYPE_ERROR":   logging.ERROR,
    "TYPE_DEBUG":   logging.DEBUG,
}


class DebugType(Enum):
    TYPE_INFO    = "INFO"
    TYPE_WARNING = "WARNING"
    TYPE_ERROR   = "ERROR"
    TYPE_DEBUG   = "DEBUG"


class DebugHelper:
    @staticmethod
    def print(
        debug_type: Literal[
            DebugType.TYPE_INFO, DebugType.TYPE_WARNING,
            DebugType.TYPE_ERROR, DebugType.TYPE_DEBUG
        ],
        debug_message: str,
        debug_module: str = None,
    ):
        module_tag = f"[{debug_module.upper()}] " if debug_module else ""
        message = f"[{debug_type.value}] {module_tag}{debug_message}"

        # Always forward to Python logger (handlers decide what to persist)
        _log.log(_PY_LEVEL.get(debug_type.name, logging.DEBUG), "%s%s", module_tag, debug_message)

        # qDebug output gated by DEBUG env var (existing behaviour)
        level = os.environ.get("DEBUG", "0")
        if level == "0":
            return
        if level == "1" and debug_type != DebugType.TYPE_ERROR:
            return
        if level == "2" and debug_type not in (DebugType.TYPE_ERROR, DebugType.TYPE_WARNING):
            return
        if level == "3" and debug_type == DebugType.TYPE_DEBUG:
            return
        qDebug(message)
