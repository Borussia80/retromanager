#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

QT_QPA_PLATFORM=offscreen DEBUG="${DEBUG:-3}" "$APP_DIR/.venv/bin/python" - <<'PY'
import os
import sqlite3
from PyQt6.QtWidgets import QApplication, QSplashScreen
from _constants import CACHE_DIR, PLATFORMS_CACHE_DB
from _tools import CacheGenerator

os.makedirs(CACHE_DIR, exist_ok=True)

# Back up existing DB
if os.path.exists(PLATFORMS_CACHE_DB):
    os.replace(PLATFORMS_CACHE_DB, f"{PLATFORMS_CACHE_DB}.bak")

app = QApplication([])
splash = QSplashScreen()
cache = CacheGenerator(app, splash)
cache.run()

db = sqlite3.connect(PLATFORMS_CACHE_DB)
platforms = db.execute("SELECT platform, COUNT(*) FROM roms GROUP BY platform ORDER BY platform").fetchall()
total = sum(n for _, n in platforms)
print(f"Platforms: {len(platforms)}")
print(f"Entries:   {total}")
for name, n in platforms:
    print(f"  {name}: {n}")
db.close()
PY
