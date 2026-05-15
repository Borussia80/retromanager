# retromanager roadmap

retromanager is being shaped into a retro library manager: simple browsing, reliable downloads for legally accessible files, local organization, and optional launcher integration.

## Phase 0 - Stabilize

- [x] Move Archive catalogue reads to the current metadata API.
- [x] Add a Linux-focused dependency file.
- [x] Store settings and cache in standard Linux user folders.
- [x] Use JSON for settings and catalogue cache.
- [x] Add a manual cache refresh script.
- [x] Surface catalogue/download failures in the UI.
- [x] Mark unavailable platforms clearly.

## Phase 1 - Clear UX

- [x] Platform list with availability and item counts.
- [x] Human-first region filters and safer search.
- [x] Hide hashes behind technical columns/details.
- [x] Add game details from double-click/context menu.
- [x] Add friendly empty/error states.
- [x] Debounce search filter for large catalogues.
- [x] Add feedback when items are added to the queue.
- [x] Apply consistent dark theme (remove qdarktheme dependency).
- [x] Rewrite About dialog with correct app identity and dark theme.
- [x] Polish download error dialog: frameless, PT-BR text, retry action.
- [x] Fix column auto-resize and format badge rendering.
- [x] Custom app icon: Atari-M style amber logo on dark background.
- [x] Full PT-BR interface translation.
- [x] Grid view with Libretro box art thumbnails (background fetch, cache).
- [x] Visual indicator for already-downloaded ROMs (list ✓ badge + grid overlay).

## Phase 2 - Reliable Downloads

- [x] Move downloads to background workers.
- [x] Stream downloads to disk instead of loading full files into RAM.
- [x] Show per-file progress and transfer speed.
- [x] Validate MD5, SHA1, and CRC32 after download.
- [x] Avoid duplicate queue entries.
- [x] Add cancel support.
- [x] Sort game list by column.
- [ ] Add retry support for failed downloads.
- [ ] Resume interrupted downloads (.part files).

## Phase 3 - Local Library

- [x] Detect already downloaded ROMs and highlight them in list and grid.
- [ ] Organize files by platform folder.
- [ ] Import existing folders into the library.
- [ ] Re-check hashes on demand.

## Phase 4 - RetroArch

- [x] Detect RetroArch config dir (native, Flatpak, Snap).
- [x] Map all 17 platforms to their default libretro cores.
- [x] Add ROM to platform `.lpl` playlist (creates file if missing, deduplicates).
- [x] Launch ROM directly in RetroArch with the correct core.
- [x] Show RetroArch status and playlist count in the sidebar integrations panel.
- [x] Context menu actions: "Abrir no RetroArch", "Adicionar à playlist".

## Phase 5 - Lutris

- [x] Detect Lutris binary and PGA database (native and Flatpak).
- [x] Add game to Lutris via installer YAML (`lutris -i`) with the linux runner.
- [x] RetroArch core path passed automatically when RetroArch is also detected.
- [x] Show Lutris status and game count in the sidebar integrations panel.
- [x] Context menu action: "Adicionar ao Lutris".

## Phase 6 - Distribution

- Package as AppImage or Flatpak.
- Install desktop entry and icons.
- Provide concise setup documentation.
