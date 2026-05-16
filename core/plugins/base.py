"""
Abstract plugin interfaces for RetroManager (FEAT-008).

Phase 1: formal interfaces extracted from existing integrations.
RetroArch and Lutris implement EmulatorPlugin.
Phase 2 (v2.3): external plugin discovery via plugin.toml.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    plugin_type: str                              # "emulator" | "metadata" | "source" | "exporter"
    capabilities: list[str] = field(default_factory=list)
    description: str = ""


class EmulatorPlugin(ABC):
    """RetroArch and Lutris implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def detected(self) -> bool: ...

    @abstractmethod
    def launch(self, platform: str, rom_path: str) -> bool: ...

    @abstractmethod
    def add_to_library(self, platform: str, rom_name: str, rom_path: str) -> bool: ...

    def library_count(self) -> int:
        return 0


class MetadataPlugin(ABC):
    """ScreenScraper, IGDB — implementations of FEAT-004."""

    @abstractmethod
    def fetch(self, platform: str, rom_name: str): ...

    @abstractmethod
    def supported_platforms(self) -> list[str]: ...

    def rate_limit_remaining(self) -> int:
        return -1


class RomSourcePlugin(ABC):
    """Archive.org is the native implementation."""

    @abstractmethod
    def search(self, platform: str, query: str) -> list: ...

    @abstractmethod
    def download_url(self, entry) -> str: ...


class ExporterPlugin(ABC):
    """Export library to other frontends (Pegasus, EmulationStation, etc.)."""

    @abstractmethod
    def export(self, roms: list[tuple[str, str]], output_dir: str) -> bool: ...

    @abstractmethod
    def format_name(self) -> str: ...
