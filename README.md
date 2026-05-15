# retromanager

retromanager is a Linux-friendly retro library manager. Browse ROM catalogues sourced from the Internet Archive, download with integrity verification, and organize your local collection. Optional integration with RetroArch and Lutris.

Use only with files and sources you are legally allowed to access.

## Run from source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linux.txt
python app.pyw
```

Refresh the ROM catalogue manually (needed on first run if no cache exists):

```bash
./refresh-cache.sh
```

## Install desktop entry (source install)

```bash
./packaging/install.sh
```

Installs icons and a `.desktop` launcher to `~/.local/share/` — no root required.

## Build AppImage

```bash
pip install pyinstaller
# Install appimagetool: https://github.com/AppImage/AppImageKit/releases
./packaging/build_appimage.sh
```

Output: `retromanager-<version>-x86_64.AppImage`

## Build Flatpak (development)

```bash
flatpak install flathub org.kde.Platform//6.7 org.kde.Sdk//6.7
flatpak install flathub org.freedesktop.Sdk.Extension.python312//24.08
flatpak-builder --user --install --force-clean build-flatpak \
    packaging/flatpak/io.github.Borussia80.retromanager.yml
```

> **Note:** regenerate `python-modules.json` with `flatpak-pip-generator` before
> submitting to Flathub (SHA256 placeholders are in the manifest).

## Data locations

| Path | Contents |
|------|----------|
| `~/.config/retromanager/settings.json` | Application settings |
| `~/.cache/retromanager/database_cache.db` | ROM catalogue (SQLite) |
| `~/.cache/retromanager/queue.json` | Persistent download queue |
| `~/.cache/retromanager/thumbnails/` | Box-art thumbnail cache (≤ 200 MB) |
| `~/.cache/retromanager/logs/` | Rotating log files |

## Roadmap

See `ROADMAP.md`.
