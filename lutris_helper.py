import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from core.plugins.base import EmulatorPlugin


_DB_CANDIDATES = [
    Path.home() / ".local" / "share" / "lutris" / "pga.db",
    Path.home() / ".var" / "app" / "net.lutris.Lutris" / "data" / "lutris" / "pga.db",
]


class LutrisHelper(EmulatorPlugin):
    """Detect Lutris and add games via installer YAML."""

    def __init__(self):
        self._exe: str | None = shutil.which("lutris")
        if not self._exe:
            # Flatpak wrapper locations (system and user)
            for prefix in (
                Path("/var/lib/flatpak/exports/bin"),
                Path.home() / ".local/share/flatpak/exports/bin",
            ):
                candidate = prefix / "net.lutris.Lutris"
                if candidate.exists():
                    self._exe = str(candidate)
                    break
        self._db: Path | None = None
        for loc in _DB_CANDIDATES:
            if loc.exists():
                self._db = loc
                break

    @property
    def name(self) -> str:
        return "Lutris"

    @property
    def detected(self) -> bool:
        return bool(self._exe or self._db)

    @property
    def exe(self) -> str | None:
        return self._exe

    def game_count(self) -> int:
        if not self._db or not self._db.exists():
            return 0
        try:
            import sqlite3
            conn = sqlite3.connect(self._db)
            cur = conn.execute("SELECT COUNT(*) FROM games WHERE installed=1")
            n = cur.fetchone()[0]
            conn.close()
            return n
        except Exception:
            return 0

    @staticmethod
    def _slug(name: str) -> str:
        clean = re.sub(r'\s*\([^)]+\)', '', name).strip()
        return re.sub(r'[^a-z0-9]+', '-', clean.lower()).strip('-')[:50]

    @staticmethod
    def _clean_name(name: str) -> str:
        return re.sub(r'\s*\([^)]+\)', '', name).strip()

    def launch(self, platform: str, rom_path: str) -> bool:
        """Launch via Lutris requires a registered game entry; not supported directly."""
        return False

    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool:
        return self.add_game(platform, rom_name, rom_path)

    def library_count(self) -> int:
        return self.game_count()

    def add_game(self, platform: str, rom_name: str, rom_path: str,
                 retroarch_exe: str | None = None,
                 core_path: str | None = None) -> bool:
        """
        Add a game to Lutris by writing a temporary installer YAML
        and calling `lutris -i <file>`. Returns False if lutris not found.
        """
        if not self._exe:
            return False

        exe = retroarch_exe or shutil.which("retroarch") or "retroarch"
        clean = self._clean_name(rom_name)
        slug = self._slug(rom_name)
        work_dir = os.path.dirname(rom_path)

        args_parts = []
        if core_path:
            args_parts += ["-L", core_path]
        args_parts.append(rom_path)
        args_str = " ".join(
            f'"{a}"' if " " in str(a) else str(a) for a in args_parts
        )

        yaml_text = yaml.dump({
            "name": clean,
            "game_slug": slug,
            "version": "RetroArch",
            "runner": "linux",
            "script": {
                "game": {
                    "exe": exe,
                    "args": args_str,
                    "working_dir": work_dir,
                }
            },
        }, allow_unicode=True)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yml", delete=False, prefix="retromanager_"
            ) as f:
                f.write(yaml_text)
                tmp_path = f.name
            subprocess.Popen([self._exe, "-i", tmp_path])
            return True
        except Exception:
            return False
