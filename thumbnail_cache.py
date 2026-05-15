import os
from urllib.parse import quote

import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from _thumbnail_evict import CACHE_DIR, evict_lru  # noqa: F401 (re-export)

THUMBNAILS_BASE = "https://thumbnails.libretro.com"

# Maps internal platform names → Libretro system names (as used on thumbnails.libretro.com)
LIBRETRO_SYSTEM: dict[str, str | None] = {
    "Nintendo - NES":                    "Nintendo - Nintendo Entertainment System",
    "Nintendo - SNES":                   "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - 64":                     "Nintendo - Nintendo 64",
    "Nintendo - GameBoy":                "Nintendo - Game Boy",
    "Nintendo - GameBoy Color":          "Nintendo - Game Boy Color",
    "Nintendo - GameBoy Advance":        "Nintendo - Game Boy Advance",
    "Nintendo - Famicom Disk":           "Nintendo - Family Computer Disk System",
    "Sega - Megadrive / Genesis":        "Sega - Mega Drive - Genesis",
    "Sega - Master System / Mark III":   "Sega - Master System - Mark III",
    "Sega - Game Gear":                  "Sega - Game Gear",
    "Sega - 32X":                        "Sega - 32X",
    "Atari 2600":                        "Atari - 2600",
    "Atari 5200":                        "Atari - 5200",
    "Atari 7800":                        "Atari - 7800",
    "NEC - PC Engine / TurboGrafx-16":   "NEC - PC Engine - TurboGrafx 16",
    "SNK - Neo Geo MVS":                 "SNK - Neo Geo",
    "Arcade - MAME":                     None,  # no standard box art in libretro
}


def _safe_filename(rom_name: str) -> str:
    """Replace filesystem-forbidden chars to match Libretro naming convention."""
    for ch in r'\/:*?"<>|':
        rom_name = rom_name.replace(ch, "_")
    return rom_name + ".png"


def get_cache_path(platform: str, rom_name: str) -> str | None:
    system = LIBRETRO_SYSTEM.get(platform)
    if not system:
        return None
    return os.path.join(CACHE_DIR, system, _safe_filename(rom_name))


def get_thumbnail_url(platform: str, rom_name: str) -> str | None:
    system = LIBRETRO_SYSTEM.get(platform)
    if not system:
        return None
    filename = _safe_filename(rom_name)
    return (
        f"{THUMBNAILS_BASE}/{quote(system, safe='')}"
        f"/Named_Boxarts/{quote(filename, safe='')}"
    )


def load_cached_path(platform: str, rom_name: str) -> str | None:
    """Returns the local path if the thumbnail exists on disk, else None."""
    path = get_cache_path(platform, rom_name)
    return path if path and os.path.exists(path) else None


class _Signals(QObject):
    done = pyqtSignal(str, str, str)   # platform, rom_name, local_path
    failed = pyqtSignal(str, str)      # platform, rom_name


class ThumbnailFetcher(QRunnable):
    """Downloads a single thumbnail to disk and emits the local path when done."""

    def __init__(self, platform: str, rom_name: str):
        super().__init__()
        self.platform = platform
        self.rom_name = rom_name
        self.signals = _Signals()
        self.setAutoDelete(True)

    def run(self):
        path = get_cache_path(self.platform, self.rom_name)
        if not path:
            return
        if os.path.exists(path):
            self.signals.done.emit(self.platform, self.rom_name, path)
            return
        url = get_thumbnail_url(self.platform, self.rom_name)
        if not url:
            return
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(resp.content)
                evict_lru()
                self.signals.done.emit(self.platform, self.rom_name, path)
            else:
                self.signals.failed.emit(self.platform, self.rom_name)
        except Exception:
            self.signals.failed.emit(self.platform, self.rom_name)
