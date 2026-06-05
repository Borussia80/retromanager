"""Shared fixtures and import stubs for all tests."""
import os
import sys
from unittest.mock import MagicMock

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Stub PyQt6 so pure-Python modules that import it can be tested
# without a Qt runtime or display server. Real Qt can be enabled for
# integration/GUI runs with RETROMANAGER_USE_REAL_PYQT=1.
if os.environ.get("RETROMANAGER_USE_REAL_PYQT") != "1":
    for _mod in (
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtNetwork",
        "PyQt6.sip",
    ):
        if _mod not in sys.modules:
            sys.modules[_mod] = MagicMock()
