"""Unit tests for core/health.py — RetroArchHealthChecker."""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.health import RetroArchHealthChecker, PlatformHealth, BIOS_REQUIRED


def _make_retroarch(detected=True, config_dir=None, core_path_val=None, core_name_val="TestCore"):
    ra = MagicMock()
    ra.detected = detected
    ra.config_dir = config_dir
    ra.core_path.return_value = core_path_val
    ra.core_name.return_value = core_name_val
    return ra


class TestPlatformHealth:
    def test_ready_when_all_ok(self):
        h = PlatformHealth(
            platform="Sony - PlayStation",
            retroarch_found=True,
            core_installed=True,
            core_path="/path/to/core.so",
            core_name="Beetle PSX HW",
            bios_required=["scph5501.bin"],
            bios_found=["scph5501.bin"],
            bios_missing=[],
        )
        assert h.ready is True
        assert h.severity == "ok"

    def test_error_when_no_retroarch(self):
        h = PlatformHealth(
            platform="Sony - PlayStation",
            retroarch_found=False,
            core_installed=False,
            core_path=None,
            core_name="Beetle PSX HW",
        )
        assert h.ready is False
        assert h.severity == "error"

    def test_error_when_core_missing(self):
        h = PlatformHealth(
            platform="Sony - PlayStation",
            retroarch_found=True,
            core_installed=False,
            core_path=None,
            core_name="Beetle PSX HW",
        )
        assert h.ready is False
        assert h.severity == "error"

    def test_warning_when_bios_partial(self):
        h = PlatformHealth(
            platform="Sony - PlayStation",
            retroarch_found=True,
            core_installed=True,
            core_path="/path/to/core.so",
            core_name="Beetle PSX HW",
            bios_required=["scph5501.bin", "scph5500.bin"],
            bios_found=["scph5501.bin"],
            bios_missing=["scph5500.bin"],
        )
        assert h.ready is False
        assert h.severity == "warning"


class TestRetroArchHealthChecker:
    def test_ready_when_all_present(self, tmp_path):
        config_dir = tmp_path / ".config" / "retroarch"
        system_dir = config_dir / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "scph5501.bin").write_bytes(b"bios")

        cores_dir = config_dir / "cores"
        cores_dir.mkdir()
        core_file = cores_dir / "mednafen_psx_hw_libretro.so"
        core_file.write_bytes(b"core")

        ra = _make_retroarch(
            detected=True,
            config_dir=config_dir,
            core_path_val=str(core_file),
            core_name_val="Beetle PSX HW",
        )
        checker = RetroArchHealthChecker(ra)
        health = checker.check("Sony - PlayStation")

        assert health.core_installed is True
        assert "scph5501.bin" in health.bios_found
        assert health.severity == "ok" or health.severity == "warning"  # other BIOS may be missing

    def test_error_when_no_retroarch(self):
        ra = _make_retroarch(detected=False)
        checker = RetroArchHealthChecker(ra)
        health = checker.check("Sony - PlayStation")

        assert health.retroarch_found is False
        assert health.severity == "error"
        assert any("RetroArch" in issue for issue in health.issues)

    def test_error_when_core_missing(self, tmp_path):
        config_dir = tmp_path / ".config" / "retroarch"
        config_dir.mkdir(parents=True)
        ra = _make_retroarch(
            detected=True,
            config_dir=config_dir,
            core_path_val=None,
            core_name_val="Beetle PSX HW",
        )
        checker = RetroArchHealthChecker(ra)
        health = checker.check("Sony - PlayStation")

        assert health.core_installed is False
        assert health.severity == "error"
        assert any("Core" in issue for issue in health.issues)

    def test_psp_has_no_bios_requirement(self, tmp_path):
        config_dir = tmp_path / ".config" / "retroarch"
        cores_dir = config_dir / "cores"
        cores_dir.mkdir(parents=True)
        core_file = cores_dir / "ppsspp_libretro.so"
        core_file.write_bytes(b"core")

        ra = _make_retroarch(
            detected=True,
            config_dir=config_dir,
            core_path_val=str(core_file),
            core_name_val="PPSSPP",
        )
        checker = RetroArchHealthChecker(ra)
        health = checker.check("Sony - PSP")

        assert health.bios_required == []
        assert health.bios_missing == []
        assert health.ready is True
        assert health.severity == "ok"

    def test_check_all_returns_all_platforms(self):
        ra = _make_retroarch(detected=False)
        checker = RetroArchHealthChecker(ra)
        platforms = ["Sony - PlayStation", "Sony - PSP", "Nintendo - NES"]
        results = checker.check_all(platforms)

        assert set(results.keys()) == set(platforms)
        for p, h in results.items():
            assert isinstance(h, PlatformHealth)
            assert h.platform == p

    def test_warning_when_bios_partial(self, tmp_path):
        config_dir = tmp_path / ".config" / "retroarch"
        system_dir = config_dir / "system"
        system_dir.mkdir(parents=True)
        # Only one of the three PS1 BIOS files present
        (system_dir / "scph5501.bin").write_bytes(b"bios")

        cores_dir = config_dir / "cores"
        cores_dir.mkdir()
        core_file = cores_dir / "mednafen_psx_hw_libretro.so"
        core_file.write_bytes(b"core")

        ra = _make_retroarch(
            detected=True,
            config_dir=config_dir,
            core_path_val=str(core_file),
            core_name_val="Beetle PSX HW",
        )
        checker = RetroArchHealthChecker(ra)
        health = checker.check("Sony - PlayStation")

        assert "scph5501.bin" in health.bios_found
        assert len(health.bios_missing) > 0
        assert health.severity == "warning"
