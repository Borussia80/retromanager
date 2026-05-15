#!/usr/bin/env bash
# Install retromanager desktop entry and icons for the current user.
# Run from the project root: ./packaging/install.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICONS_SRC="$APP_DIR/resources/icons"
SHARE="$HOME/.local/share"

echo "Installing retromanager for $USER…"

# Icons
for size in 16 32 48 64 128 256 512; do
    dest="$SHARE/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$dest"
    cp "$ICONS_SRC/icon_${size}.png" "$dest/retromanager.png"
done
echo "  ✓ Icons installed"

# Desktop entry (patch Exec to point at run.sh)
DESKTOP_DEST="$SHARE/applications"
mkdir -p "$DESKTOP_DEST"
sed "s|Exec=retromanager|Exec=$APP_DIR/run.sh|" \
    "$APP_DIR/packaging/retromanager.desktop" \
    > "$DESKTOP_DEST/retromanager.desktop"
echo "  ✓ Desktop entry installed ($DESKTOP_DEST/retromanager.desktop)"

# Refresh caches
command -v update-desktop-database &>/dev/null && \
    update-desktop-database "$DESKTOP_DEST" && \
    echo "  ✓ Desktop database updated"
command -v gtk-update-icon-cache &>/dev/null && \
    gtk-update-icon-cache -f -t "$SHARE/icons/hicolor" && \
    echo "  ✓ Icon cache updated"

echo "Done. Launch via your application menu or: $APP_DIR/run.sh"
