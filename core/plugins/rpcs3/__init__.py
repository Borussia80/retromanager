"""RPCS3 emulator plugin — launcher-only for PS3.

PS3 has no download source in RetroManager (legal reasons). This plugin
detects RPCS3 and launches games the user has provided themselves.
add_to_library() returns False intentionally — RPCS3 manages its library
internally. Games show up in the sidebar only when the user adds a PS3
folder via Opções > Importar pasta de ROMs.
"""
import shutil
import subprocess
from pathlib import Path

from core.plugins.base import EmulatorPlugin


class RPCS3Plugin(EmulatorPlugin):

    @property
    def name(self) -> str:
        return "RPCS3"

    def detected(self) -> bool:
        if shutil.which("rpcs3"):
            return True
        flatpak_path = (
            Path.home() / ".local" / "share" / "flatpak" / "exports" / "bin" / "net.rpcs3.RPCS3"
        )
        return flatpak_path.exists()

    def launch(self, platform: str, rom_path: str) -> bool:
        exe = shutil.which("rpcs3") or "rpcs3"
        # RPCS3 requires EBOOT.BIN inside the game's directory structure
        eboot = next(Path(rom_path).rglob("EBOOT.BIN"), None)
        subprocess.Popen([exe, "--no-gui", str(eboot or rom_path)])
        return True

    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool:
        return False   # RPCS3 manages its own game library

    def library_count(self) -> int:
        return 0


def create_plugin() -> RPCS3Plugin:
    return RPCS3Plugin()
