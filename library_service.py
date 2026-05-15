"""
Pure business-logic helpers extracted from MainWindow.

No Qt dependency — all functions are plain Python and fully unit-testable.
"""

import os
import re


def scan_downloaded(settings, platform: str | None = None) -> set[str]:
    """Return stems of ROM files present in the download dir and import paths."""
    base = settings.get('download_path')
    dirs_to_scan = [base]
    if platform:
        dirs_to_scan.append(os.path.join(base, platform))
    for imp in settings.get('import_paths'):
        dirs_to_scan.append(imp)
        if platform:
            dirs_to_scan.append(os.path.join(imp, platform))

    stems: set[str] = set()
    for d in dirs_to_scan:
        try:
            for f in os.listdir(d):
                if os.path.isfile(os.path.join(d, f)):
                    stems.add(os.path.splitext(f)[0])
        except OSError:
            pass
    return stems


def find_rom_file(settings, rom_name: str, platform: str | None) -> str | None:
    """Find a downloaded ROM file by stem, checking platform subdir, base dir, and import paths."""
    base = settings.get('download_path')
    dirs: list[str] = []
    if platform:
        dirs.append(os.path.join(base, platform))
    dirs.append(base)
    for imp in settings.get('import_paths'):
        if platform:
            dirs.append(os.path.join(imp, platform))
        dirs.append(imp)

    for d in dirs:
        try:
            entries = os.listdir(d)
        except OSError:
            continue
        # Prefer extracted (non-archive) files
        for f in entries:
            stem, ext = os.path.splitext(f)
            if stem == rom_name and ext.lower() not in ('.zip', '.7z', '.part'):
                full = os.path.join(d, f)
                if os.path.isfile(full):
                    return full
        # Fall back to archive
        for f in entries:
            stem, ext = os.path.splitext(f)
            if stem == rom_name and ext.lower() in ('.zip', '.7z'):
                full = os.path.join(d, f)
                if os.path.isfile(full):
                    return full
    return None


def rom_matches_filters(rom_name: str, keywords: list[str], region: str | None,
                        shortname: str = "") -> bool:
    """Return True if the ROM passes the active keyword and region filters."""
    target = rom_name.lower()
    if region and f"({region})".lower() not in target:
        return False
    if not keywords:
        return True
    alt = shortname.lower()
    return all(kw in target or (alt and kw in alt) for kw in keywords)


def build_rom_summary(platform_name: str, rom_name: str, rom_data: dict,
                      size_formatter=None) -> str:
    """Build a human-readable tooltip / detail string for a ROM."""
    tags = re.findall(r'\(([^)]+)\)', rom_name)
    tags_text = ", ".join(tags) if tags else "—"
    size = rom_data.get('size', 0)
    size_str = size_formatter(size) if size_formatter else str(size)
    return (
        f"{rom_name}\n"
        f"Plataforma: {platform_name}\n"
        f"Tags: {tags_text}\n"
        f"Tamanho: {size_str}\n"
        f"Formato: {rom_data.get('format', '—')}"
    )
