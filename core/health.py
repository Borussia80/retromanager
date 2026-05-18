"""RetroArch health checker — validates core and BIOS availability per platform."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

_log = logging.getLogger("retromanager.health")

BIOS_REQUIRED: dict[str, list[str]] = {
    "Sony - PlayStation":              ["scph5501.bin", "scph5500.bin", "scph5502.bin"],
    "Sony - PlayStation 2":            ["ps2-0230a-20080220.bin"],
    "Sony - PSP":                      [],
    "Nintendo - Famicom Disk":         ["disksys.rom"],
    "NEC - PC Engine / TurboGrafx-16": ["syscard3.pce"],
    "SNK - Neo Geo MVS":               ["neogeo.zip"],
    "Arcade - MAME":                   [],
}


@dataclass
class PlatformHealth:
    platform: str
    retroarch_found: bool
    core_installed: bool
    core_path: str | None
    core_name: str
    bios_dir: str | None = None       # path to RetroArch system/ dir for BIOS placement
    bios_required: list[str] = field(default_factory=list)
    bios_found: list[str] = field(default_factory=list)
    bios_missing: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.retroarch_found and self.core_installed and not self.bios_missing

    @property
    def severity(self) -> str:
        if self.ready:
            return "ok"
        if not self.retroarch_found or not self.core_installed:
            return "error"
        return "warning"   # RetroArch + core ok, but BIOS partially missing


class RetroArchHealthChecker:
    def __init__(self, retroarch) -> None:
        self._ra = retroarch

    def check(self, platform: str) -> PlatformHealth:
        """Check RetroArch readiness for platform: installation, core, and BIOS files.

        Returns a PlatformHealth with severity 'ok', 'warning', or 'error'.
        'warning' means RetroArch and core are present but at least one BIOS file is missing.
        'error' means RetroArch or the core itself is not installed.
        """
        bios_dir: Path | None = (
            (self._ra.config_dir / "system") if self._ra.config_dir else None
        )
        health = PlatformHealth(
            platform=platform,
            retroarch_found=self._ra.detected,
            core_installed=False,
            core_path=None,
            core_name=self._ra.core_name(platform),
            bios_dir=str(bios_dir) if bios_dir else None,
            bios_required=list(BIOS_REQUIRED.get(platform, [])),
        )

        if not self._ra.detected:
            health.issues.append("RetroArch não encontrado.")
            return health

        core_path = self._ra.core_path(platform)
        health.core_installed = bool(core_path)
        health.core_path = core_path
        if not health.core_installed:
            health.issues.append(
                f"Core '{health.core_name}' não instalado. "
                "Instale via RetroArch → Núcleos Online."
            )

        for bios_file in health.bios_required:
            if bios_dir and (bios_dir / bios_file).exists():
                health.bios_found.append(bios_file)
            else:
                health.bios_missing.append(bios_file)
                health.issues.append(f"BIOS ausente: {bios_file}")

        return health

    def check_all(self, platforms: list[str]) -> dict[str, PlatformHealth]:
        """Run check() for each platform and return results keyed by platform name."""
        return {p: self.check(p) for p in platforms}
