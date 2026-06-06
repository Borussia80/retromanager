import json
import logging
import re
import shutil
import subprocess
from pathlib import Path

from core.plugins.base import EmulatorPlugin

_log = logging.getLogger("retromanager.retroarch")


CORE_MAP: dict[str, tuple[str, str]] = {
    "Nintendo - NES":                   ("fceumm_libretro.so",           "FCEUmm"),
    "Nintendo - SNES":                  ("snes9x_libretro.so",           "Snes9x"),
    "Nintendo - 64":                    ("mupen64plus_next_libretro.so", "Mupen64Plus-Next"),
    "Nintendo - GameBoy":               ("gambatte_libretro.so",         "Gambatte"),
    "Nintendo - GameBoy Color":         ("gambatte_libretro.so",         "Gambatte"),
    "Nintendo - GameBoy Advance":       ("mgba_libretro.so",             "mGBA"),
    "Nintendo - Famicom Disk":          ("fceumm_libretro.so",           "FCEUmm"),
    "Sega - Megadrive / Genesis":       ("genesis_plus_gx_libretro.so",  "Genesis Plus GX"),
    "Sega - Master System / Mark III":  ("genesis_plus_gx_libretro.so",  "Genesis Plus GX"),
    "Sega - Game Gear":                 ("genesis_plus_gx_libretro.so",  "Genesis Plus GX"),
    "Sega - 32X":                       ("picodrive_libretro.so",        "PicoDrive"),
    "Atari 2600":                       ("stella2014_libretro.so",       "Stella 2014"),
    "Atari 5200":                       ("atari800_libretro.so",         "Atari800"),
    "Atari 7800":                       ("prosystem_libretro.so",        "ProSystem"),
    "NEC - PC Engine / TurboGrafx-16":  ("mednafen_pce_libretro.so",    "Beetle PCE"),
    "SNK - Neo Geo MVS":                ("fbneo_libretro.so",            "FinalBurn Neo"),
    "Arcade - MAME":                    ("mame2003_plus_libretro.so",   "MAME 2003-Plus"),
    "Sony - PlayStation":               ("mednafen_psx_hw_libretro.so", "Beetle PSX HW"),
    "Sony - PlayStation 2":             ("pcsx2_libretro.so",           "PCSX2"),
    "Sony - PSP":                       ("ppsspp_libretro.so",          "PPSSPP"),
}

SYSTEM_MAP: dict[str, str] = {
    "Nintendo - NES":                   "Nintendo - Nintendo Entertainment System",
    "Nintendo - SNES":                  "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - 64":                    "Nintendo - Nintendo 64",
    "Nintendo - GameBoy":               "Nintendo - Game Boy",
    "Nintendo - GameBoy Color":         "Nintendo - Game Boy Color",
    "Nintendo - GameBoy Advance":       "Nintendo - Game Boy Advance",
    "Nintendo - Famicom Disk":          "Nintendo - Family Computer Disk System",
    "Sega - Megadrive / Genesis":       "Sega - Mega Drive - Genesis",
    "Sega - Master System / Mark III":  "Sega - Master System - Mark III",
    "Sega - Game Gear":                 "Sega - Game Gear",
    "Sega - 32X":                       "Sega - 32X",
    "Atari 2600":                       "Atari - 2600",
    "Atari 5200":                       "Atari - 5200",
    "Atari 7800":                       "Atari - 7800",
    "NEC - PC Engine / TurboGrafx-16":  "NEC - PC Engine - TurboGrafx 16",
    "SNK - Neo Geo MVS":                "SNK - Neo Geo",
    "Arcade - MAME":                    "MAME",
    "Sony - PlayStation":               "Sony - PlayStation",
    "Sony - PlayStation 2":             "Sony - PlayStation 2",
    "Sony - PSP":                       "Sony - PlayStation Portable",
}

_CONFIG_CANDIDATES = [
    Path.home() / ".config" / "retroarch",
    Path.home() / ".var" / "app" / "org.libretro.RetroArch" / "config" / "retroarch",
    Path.home() / "snap" / "retroarch" / "current" / ".config" / "retroarch",
]


class RetroArchHelper(EmulatorPlugin):
    """Detect RetroArch and manage playlists / launch."""

    def __init__(self):
        self._config_dir: Path | None = None
        self._exe: str | None = None
        self._detect()

    def _detect(self):
        for loc in _CONFIG_CANDIDATES:
            if loc.is_dir():
                self._config_dir = loc
                break
        self._exe = shutil.which("retroarch")
        if not self._exe and self._config_dir:
            for name in ("retroarch", "retroarch-x86_64.AppImage"):
                c = self._config_dir.parent / name
                if c.exists() and c.is_file():
                    self._exe = str(c)
                    break
        if not self._exe:
            # Flatpak wrapper locations (system and user)
            for prefix in (
                Path("/var/lib/flatpak/exports/bin"),
                Path.home() / ".local/share/flatpak/exports/bin",
            ):
                candidate = prefix / "org.libretro.RetroArch"
                if candidate.exists():
                    self._exe = str(candidate)
                    break

    @property
    def name(self) -> str:
        return "RetroArch"

    @property
    def detected(self) -> bool:
        return bool(self._config_dir or self._exe)

    @property
    def exe(self) -> str | None:
        return self._exe

    @property
    def config_dir(self) -> Path | None:
        return self._config_dir

    def _cores_dir(self) -> Path | None:
        return (self._config_dir / "cores") if self._config_dir else None

    def core_path(self, platform: str) -> str | None:
        cd = self._cores_dir()
        if not cd:
            return None
        fname, _ = CORE_MAP.get(platform, (None, None))
        if not fname:
            return None
        p = cd / fname
        return str(p) if p.exists() else None

    def core_name(self, platform: str) -> str:
        return CORE_MAP.get(platform, (None, "?"))[1]

    def total_playlist_items(self) -> int:
        if not self._config_dir:
            return 0
        pd = self._config_dir / "playlists"
        if not pd.exists():
            return 0
        total = 0
        for lpl in pd.glob("*.lpl"):
            try:
                with open(lpl) as f:
                    data = json.load(f)
                total += len(data.get("items", []))
            except Exception as exc:
                _log.warning("Playlist inválida ignorada (%s): %s", lpl.name, exc)
        return total

    def launch(self, platform: str, rom_path: str) -> bool:
        if not self._exe:
            _log.warning("launch called but no RetroArch executable was detected")
            return False
        core = self.core_path(platform)
        cmd = [self._exe]
        if self._config_dir:
            cmd += ["-c", str(self._config_dir / "retroarch.cfg")]
        if core:
            cmd += ["-L", core]
        cmd.append(rom_path)
        _log.debug("launching: %s", " ".join(cmd))
        try:
            subprocess.Popen(cmd)
            return True
        except OSError as e:
            _log.error("RetroArch launch failed: %s", e)
            return False

    def add_to_playlist(self, platform: str, rom_name: str, rom_path: str) -> bool:
        if not self._config_dir:
            return False
        sys_name = SYSTEM_MAP.get(platform, platform)
        pd = self._config_dir / "playlists"
        pd.mkdir(parents=True, exist_ok=True)
        ppath = pd / f"{sys_name}.lpl"

        if ppath.exists():
            try:
                with open(ppath) as f:
                    data = json.load(f)
            except Exception:
                data = self._empty_playlist()
        else:
            data = self._empty_playlist()

        for item in data["items"]:
            if item.get("path") == rom_path:
                return True

        core = self.core_path(platform) or "DETECT"
        clean = re.sub(r'\s*\([^)]+\)', '', rom_name).strip()
        data["items"].append({
            "path": rom_path,
            "label": clean,
            "core_path": core,
            "core_name": self.core_name(platform),
            "crc32": "00000000|crc",
            "db_name": f"{sys_name}.lpl",
        })
        try:
            with open(ppath, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool:
        return self.add_to_playlist(platform, rom_name, rom_path)

    def library_count(self) -> int:
        return self.total_playlist_items()

    @staticmethod
    def _empty_playlist() -> dict:
        return {
            "version": "1.4",
            "default_core_path": "",
            "default_core_name": "",
            "label_display_mode": 0,
            "right_thumbnail_mode": 0,
            "left_thumbnail_mode": 0,
            "sort_mode": 0,
            "items": [],
        }
