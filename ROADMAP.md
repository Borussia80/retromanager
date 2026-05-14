# retromanager roadmap

retromanager is being shaped into a retro library manager: simple browsing, reliable downloads for legally accessible files, local organization, and optional launcher integration.

## Phase 0 - Stabilize

- [x] Move Archive catalogue reads to the current metadata API.
- [x] Add a Linux-focused dependency file.
- [x] Store settings and cache in standard Linux user folders.
- [x] Use JSON for settings and catalogue cache.
- [x] Add a manual cache refresh script.
- [ ] Surface catalogue/download failures in the UI.
- [ ] Mark unavailable platforms clearly.

## Phase 1 - Clear UX

- Platform list with availability and item counts.
- Human-first filters for region, language, and release type.
- Hide hashes in an advanced details panel.
- Add friendly empty/error states.

## Phase 2 - Reliable Downloads

- Move downloads to background workers.
- Show per-file and total progress.
- Add retry/cancel support.
- Stream files to disk and validate hashes after download.
- Avoid duplicate queue entries.

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
