# Community announcement posts — RetroManager v2.3.2

Use these when posting to communities. Adapt tone per platform.

---

## Reddit — r/linux_gaming  r/emulation  r/linux

**Title:**
> RetroManager v2.3.2 — browse & download retro ROMs from Archive.org on Linux (PyQt6, AppImage)

**Body:**
> I've been building a ROM manager for Linux and just released v2.3.2.
>
> **What it does:**
> - Browse and download ROMs directly from Archive.org (NES, SNES, N64, GB/GBC/GBA, Sega, Atari, NEC, SNK, MAME, PlayStation, PS2, PSP)
> - RetroArch health check — shows ✅/⚠️/❌ per platform so you know if cores and BIOS files are installed before downloading
> - Full-text search across 40k+ ROMs (SQLite FTS5, sub-100ms)
> - Concurrent downloads with resume, exponential retry, and hash verification (SHA1/MD5/CRC32)
> - Favorites, history, cover art thumbnails, Lutris integration
> - Dark PyQt6 UI, ships as a self-contained AppImage
>
> **GitHub:** https://github.com/Borussia80/retromanager
> **Download:** https://github.com/Borussia80/retromanager/releases/tag/v2.3.2
>
> Feedback, bug reports and PRs very welcome!

---

## Lemmy — lemmy.ml/c/linux_gaming  or  feddit.de/c/emulation

Same text as Reddit — Lemmy renders Markdown identically.

---

## Discord servers to post in

- **RetroArch** official Discord → #tools-and-utilities
- **Lutris** Discord → #general or #tools
- **Linux Gamers** (various servers) → #projects or #tools

**Short message for Discord:**
> 🕹️ **RetroManager v2.3.2** — Linux ROM manager that browses/downloads from Archive.org
> Supports NES/SNES/N64/GB/GBC/GBA/Sega/Atari/MAME/PS1/PS2/PSP · RetroArch health check · Lutris integration · AppImage
> https://github.com/Borussia80/retromanager

---

## Mastodon / Fediverse

> 🕹️ Released RetroManager v2.3.2 — a Linux ROM manager that browses & downloads from Archive.org.
>
> ✅ Supports 13 platforms (NES → PSP)
> ✅ RetroArch health check per platform
> ✅ Full-text search across 40k+ ROMs
> ✅ Hash verification on every download
> ✅ Lutris integration
> ✅ Ships as AppImage
>
> 🔗 https://github.com/Borussia80/retromanager
>
> #linux #retroGaming #emulation #retroarch #python #opensource #gamedev

---

## AppImage Hub

Submit at: https://github.com/AppImage/appimage.github.io
(open a PR adding a YAML file under `apps/retromanager.yml`)

```yaml
---
name: RetroManager
description: Linux retro ROM manager — browse, download and launch classic games from Archive.org
categories:
  - Game
  - Utility
authors:
  - name: Borussia80
    url: https://github.com/Borussia80
license: MIT
links:
  - type: GitHub
    url: https://github.com/Borussia80/retromanager
  - type: Download
    url: https://github.com/Borussia80/retromanager/releases
screenshots:
  - https://raw.githubusercontent.com/Borussia80/retromanager/main/docs/screenshots/rom_list.png
  - https://raw.githubusercontent.com/Borussia80/retromanager/main/docs/screenshots/grid_view.png
  - https://raw.githubusercontent.com/Borussia80/retromanager/main/docs/screenshots/download.png
```
