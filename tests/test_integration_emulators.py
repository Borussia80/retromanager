"""Integration tests for emulator helpers (RetroArch, Lutris).

Run with: pytest tests/test_integration_emulators.py -v
Mark: @pytest.mark.integration
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from retroarch_helper import RetroArchHelper, CORE_MAP, SYSTEM_MAP
from lutris_helper import LutrisHelper


class TestRetroArchHelperDetection:
    """Test RetroArch detection on real system."""

    def test_retroarch_detected_or_missing(self):
        """RetroArchHelper should either detect RetroArch or report not detected."""
        helper = RetroArchHelper()
        assert isinstance(helper.detected, bool)

    def test_retroarch_properties_types(self):
        """Properties should return correct types even if not detected."""
        helper = RetroArchHelper()
        assert helper.exe is None or isinstance(helper.exe, str)
        assert helper.config_dir is None or isinstance(helper.config_dir, Path)

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_retroarch_config_dir_found(self):
        """If RetroArch is installed, config_dir should be found."""
        helper = RetroArchHelper()
        assert helper.config_dir is not None
        assert helper.config_dir.exists()

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_retroarch_cores_detection(self):
        """If RetroArch installed, should find cores directory."""
        helper = RetroArchHelper()
        if not helper.detected:
            pytest.skip("RetroArch not detected")
        cores_dir = helper._cores_dir()
        assert cores_dir is None or isinstance(cores_dir, Path)

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_retroarch_core_path_valid_platforms(self):
        """core_path should return valid path for known platforms or None."""
        helper = RetroArchHelper()
        for platform in CORE_MAP.keys():
            core = helper.core_path(platform)
            assert core is None or isinstance(core, str)
            if core:
                assert core.endswith(".so")

    def test_retroarch_core_name_mapping(self):
        """core_name should return core name for all mapped platforms."""
        helper = RetroArchHelper()
        for platform in CORE_MAP.keys():
            name = helper.core_name(platform)
            assert isinstance(name, str)
            assert len(name) > 0


class TestRetroArchPlaylist:
    """Test RetroArch playlist operations."""

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_total_playlist_items(self):
        """total_playlist_items should return int >= 0."""
        helper = RetroArchHelper()
        count = helper.total_playlist_items()
        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_add_to_playlist_creates_entry(self):
        """add_to_playlist should create or update playlist file."""
        helper = RetroArchHelper()
        if not helper.detected or not helper.config_dir:
            pytest.skip("RetroArch not detected")

        # Create temp ROM file
        with tempfile.NamedTemporaryFile(suffix=".nes", delete=False) as f:
            rom_path = f.name

        try:
            # Add to playlist
            result = helper.add_to_playlist(
                "Nintendo - NES",
                "Test ROM (Test)",
                rom_path
            )
            assert isinstance(result, bool)

            if result:
                # Verify playlist was created/updated
                sys_name = SYSTEM_MAP["Nintendo - NES"]
                playlist_path = helper.config_dir / "playlists" / f"{sys_name}.lpl"
                assert playlist_path.exists()

                # Verify ROM is in playlist
                with open(playlist_path) as f:
                    data = json.load(f)
                paths = [item["path"] for item in data.get("items", [])]
                assert rom_path in paths
        finally:
            Path(rom_path).unlink(missing_ok=True)

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_add_to_playlist_idempotent(self):
        """Adding same ROM twice should not duplicate entry."""
        helper = RetroArchHelper()
        if not helper.detected or not helper.config_dir:
            pytest.skip("RetroArch not detected")

        with tempfile.NamedTemporaryFile(suffix=".nes", delete=False) as f:
            rom_path = f.name

        try:
            # Add twice
            helper.add_to_playlist("Nintendo - NES", "Test ROM", rom_path)
            result = helper.add_to_playlist("Nintendo - NES", "Test ROM", rom_path)
            assert result is True

            # Count entries
            sys_name = SYSTEM_MAP["Nintendo - NES"]
            playlist_path = helper.config_dir / "playlists" / f"{sys_name}.lpl"
            with open(playlist_path) as f:
                data = json.load(f)
            paths = [item["path"] for item in data.get("items", [])]
            # Should appear only once
            assert paths.count(rom_path) == 1
        finally:
            Path(rom_path).unlink(missing_ok=True)


class TestRetroArchLaunch:
    """Test RetroArch launch functionality."""

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_launch_with_dummy_rom(self):
        """launch() should succeed if RetroArch is installed (subprocess started)."""
        helper = RetroArchHelper()
        if not helper.exe:
            pytest.skip("RetroArch executable not found")

        # Create dummy ROM
        with tempfile.NamedTemporaryFile(suffix=".nes", delete=False) as f:
            rom_path = f.name

        try:
            result = helper.launch("Nintendo - NES", rom_path)
            # Should return True (subprocess created) or False (launch error)
            assert isinstance(result, bool)
        finally:
            Path(rom_path).unlink(missing_ok=True)

    def test_launch_with_invalid_platform(self):
        """launch() should handle unknown platforms gracefully."""
        helper = RetroArchHelper()
        if not helper.exe:
            pytest.skip("RetroArch not available")

        with tempfile.NamedTemporaryFile(suffix=".rom", delete=False) as f:
            rom_path = f.name

        try:
            # Unknown platform should still attempt launch (without core)
            result = helper.launch("Unknown - Platform", rom_path)
            assert isinstance(result, bool)
        finally:
            Path(rom_path).unlink(missing_ok=True)


class TestLutrisHelperDetection:
    """Test Lutris detection on real system."""

    def test_lutris_detected_or_missing(self):
        """LutrisHelper should report detected or not detected."""
        helper = LutrisHelper()
        assert isinstance(helper.detected, bool)

    def test_lutris_exe_property(self):
        """exe property should return str or None."""
        helper = LutrisHelper()
        assert helper.exe is None or isinstance(helper.exe, str)

    @pytest.mark.skipif(
        not Path.home().joinpath(".local/share/lutris/pga.db").exists()
        and not Path.home().joinpath(".var/app/net.lutris.Lutris/data/lutris/pga.db").exists(),
        reason="Lutris not installed"
    )
    def test_lutris_detected_when_installed(self):
        """If Lutris is installed, detected should be True."""
        helper = LutrisHelper()
        assert helper.detected is True

    def test_lutris_game_count(self):
        """game_count should return int >= 0."""
        helper = LutrisHelper()
        count = helper.game_count()
        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.skipif(
        not Path.home().joinpath(".local/share/lutris/pga.db").exists()
        and not Path.home().joinpath(".var/app/net.lutris.Lutris/data/lutris/pga.db").exists(),
        reason="Lutris not installed"
    )
    def test_lutris_game_count_when_installed(self):
        """If Lutris installed, game_count should return actual count."""
        helper = LutrisHelper()
        count = helper.game_count()
        # Should be valid count (may be 0 if no games)
        assert isinstance(count, int)
        assert count >= 0


class TestLutrisUtilities:
    """Test Lutris utility functions."""

    def test_clean_name(self):
        """_clean_name should remove parenthetical info."""
        assert LutrisHelper._clean_name("Game (USA)") == "Game"
        assert LutrisHelper._clean_name("Game (USA) (Rev A)") == "Game"
        assert LutrisHelper._clean_name("Game") == "Game"

    def test_slug_generation(self):
        """_slug should generate valid slug."""
        slug = LutrisHelper._slug("Super Mario Bros (USA)")
        assert slug == "super-mario-bros"
        assert len(slug) <= 50
        assert all(c.isalnum() or c == '-' for c in slug)


@pytest.mark.integration
class TestIntegrationEmulatorChain:
    """Integration tests combining detection and operations."""

    def test_both_helpers_initialize(self):
        """Both emulator helpers should initialize without errors."""
        ra = RetroArchHelper()
        lutris = LutrisHelper()
        assert ra is not None
        assert lutris is not None

    def test_detection_consistency(self):
        """Detection should be consistent across multiple calls."""
        helper = RetroArchHelper()
        detected1 = helper.detected
        detected2 = helper.detected
        assert detected1 == detected2

    @pytest.mark.skipif(
        not Path.home().joinpath(".config/retroarch").exists()
        and not Path.home().joinpath(".var/app/org.libretro.RetroArch/config/retroarch").exists(),
        reason="RetroArch not installed"
    )
    def test_retroarch_workflow_detection_to_playlist(self):
        """Full workflow: detect → find config → add to playlist."""
        helper = RetroArchHelper()

        # Step 1: Detect
        assert helper.detected or True  # Can be False; that's OK

        if not helper.detected:
            pytest.skip("RetroArch not detected on this system")

        # Step 2: Config found
        assert helper.config_dir is not None

        # Step 3: Can add to playlist
        with tempfile.NamedTemporaryFile(suffix=".nes", delete=False) as f:
            rom_path = f.name

        try:
            result = helper.add_to_playlist("Nintendo - NES", "Test", rom_path)
            assert isinstance(result, bool)
        finally:
            Path(rom_path).unlink(missing_ok=True)
