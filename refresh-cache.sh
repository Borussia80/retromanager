#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

QT_QPA_PLATFORM=offscreen DEBUG="${DEBUG:-3}" "$APP_DIR/.venv/bin/python" - <<'PY'
import json
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from _constants import CACHE_DIR, PLATFORMS_CACHE_FILENAME
from _tools import CacheGenerator

os.makedirs(CACHE_DIR, exist_ok=True)
if os.path.exists(PLATFORMS_CACHE_FILENAME):
    os.replace(PLATFORMS_CACHE_FILENAME, f"{PLATFORMS_CACHE_FILENAME}.bak")

app = QApplication([])
splash = QSplashScreen()
cache = CacheGenerator(app, splash)
cache.run()

with open(PLATFORMS_CACHE_FILENAME, "r", encoding="utf-8") as fp:
    data = json.load(fp)

print(f"Platforms: {len(data)}")
print(f"Entries: {sum(len(roms) for roms in data.values())}")
for name, roms in data.items():
    print(f"{name}: {len(roms)}")
PY
