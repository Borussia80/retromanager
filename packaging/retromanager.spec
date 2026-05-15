# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for retromanager.
# Usage (from project root, with venv active):
#   pyinstaller packaging/retromanager.spec
#
# Output: dist/retromanager/   (onedir bundle)

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(PROJECT_ROOT, "app.pyw")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        # Qt resource archive (icons, etc.)
        (os.path.join(PROJECT_ROOT, "resources.rcc"), "."),
        # Raw icon files (used by ICONS_DIR at startup)
        (os.path.join(PROJECT_ROOT, "resources", "icons"), "resources/icons"),
    ],
    hiddenimports=[
        # Explicitly imported Qt modules not always auto-detected
        "PyQt6.QtNetwork",
        "PyQt6.QtSvg",
        "PyQt6.QtXml",
        # py7zr is imported inside functions
        "py7zr",
        "py7zr.py7zr",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PyInstaller",
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="retromanager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(PROJECT_ROOT, "resources", "icons", "icon_256.png"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="retromanager",
)
