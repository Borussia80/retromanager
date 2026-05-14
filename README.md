# retromanager

retromanager is a Linux-friendly retro library manager evolving from the NoIntro ROMs Downloader 2.0 RC1 codebase.

The goal is to make retro-library workflows easier to understand: browse available catalogues, organize local files, verify metadata, and eventually integrate with RetroArch and Lutris. Use it only with files and sources you are legally allowed to access.

## Current status

This is an early fork/foundation pass. The first stabilization work is underway:

- Archive catalogue reads use `https://archive.org/metadata/...`.
- Settings are stored in `~/.config/retromanager/settings.json`.
- Catalogue cache is stored in `~/.cache/retromanager/database_cache.json`.
- A Linux dependency file is available at `requirements-linux.txt`.
- A manual cache refresh script is available at `refresh-cache.sh`.

Some Archive items no longer expose public file lists. retromanager keeps those platforms in the catalogue for now, but they may show zero available entries.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --ignore-requires-python -r requirements-linux.txt
python app.pyw
```

Refresh the catalogue manually:

```bash
./refresh-cache.sh
```

## Roadmap

See `ROADMAP.md`.
