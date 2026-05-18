<p align="center">
  <img src="docs/wordmark.png" alt="RetroManager" width="480" />
</p>

<p align="center">
  <strong>Linux retro ROM manager — browse, download and launch classic games from Archive.org</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/github/v/release/Borussia80/retromanager?style=flat-square&color=f5a524" alt="Latest release" />
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/PyQt6-6.6%2B-41cd52?style=flat-square" alt="PyQt6" />
  <img src="https://img.shields.io/badge/platform-Linux-informational?style=flat-square" alt="Linux" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT" />
</p>

---

## Features

- **Browse & download** ROMs from Archive.org — Nintendo, Sega, Atari, SNK, NEC, Arcade (MAME), Sony PlayStation / PS2 / PSP
- **RetroArch health check** — shows ✅/⚠️/❌ per platform; detects missing cores and BIOS files before you download
- **Full-text search** (SQLite FTS5) across tens of thousands of ROMs with sub-100 ms response
- **Concurrent downloads** with exponential retry, resume on reconnect, and SHA1/MD5/CRC32 verification
- **Favorites & history** — star ROMs, track what you've played
- **Lutris integration** — add games to your Lutris library with one click
- **Thumbnail gallery** — fetches cover art from the libretro-thumbnails database
- **Dark UI** built with PyQt6

## Supported platforms

| System | Format | Source |
|---|---|---|
| Nintendo NES | ZIP | No-Intro / Myrient |
| Nintendo SNES | ZIP | No-Intro |
| Nintendo 64 | ZIP | No-Intro |
| Nintendo Game Boy / GBC / GBA | ZIP | No-Intro |
| Nintendo Famicom Disk System | ZIP | No-Intro |
| Sega Master System / 32X / Mega Drive / Game Gear | 7z | No-Intro |
| Atari 2600 / 5200 / 7800 | 7z | No-Intro |
| NEC PC Engine / TurboGrafx-16 | 7z | No-Intro |
| SNK Neo Geo MVS | ZIP | No-Intro |
| Arcade (MAME) | ZIP | MAME merged set |
| Sony PlayStation | ZIP | Redump / Hearto 2024 |
| Sony PlayStation 2 | CHD | Redump (split by letter) |
| Sony PSP | CHD | Redump |

## Requirements

- Linux (x86_64)
- [RetroArch](https://www.retroarch.com/) — for launching ROMs (optional but recommended)

## Installation

### AppImage (recommended)

Download the latest `retromanager-x.x.x-x86_64.AppImage` from the [Releases](https://github.com/Borussia80/retromanager/releases) page:

```bash
chmod +x retromanager-2.3.2-x86_64.AppImage
./retromanager-2.3.2-x86_64.AppImage
```

### From source

```bash
git clone https://github.com/Borussia80/retromanager.git
cd retromanager
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python app.pyw
```

## First run

1. Launch the app — it will create `~/.config/retromanager/` and `~/.cache/retromanager/`
2. Click **File → Refresh catalog** to download the ROM index from Archive.org (~30 seconds)
3. Select a platform in the sidebar, browse ROMs, and click **Download**
4. Optionally install [RetroArch](https://www.retroarch.com/) and the matching core to launch ROMs directly

## Development

```bash
# Run tests
pytest tests/ -v

# Lint
ruff check .

# Build AppImage
bash packaging/build_appimage.sh
```

## License

MIT — see [LICENSE](LICENSE)
