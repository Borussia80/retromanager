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

- Organize files by platform.
- Detect already downloaded ROMs.
- Import existing folders.
- Re-check hashes on demand.

## Phase 4 - RetroArch

- Detect RetroArch config and playlist paths.
- Map platforms to cores/playlists.
- Generate or update `.lpl` playlists.
- Launch selected games through RetroArch.

## Phase 5 - Lutris

- Detect Lutris.
- Create launcher entries from local library items.
- Export/import launcher configuration.

## Phase 6 - Distribution

- Package as AppImage or Flatpak.
- Install desktop entry and icons.
- Provide concise setup documentation.
