#!/usr/bin/env bash
# Build a retromanager AppImage.
#
# Prerequisites (install once):
#   pip install pyinstaller
#   wget -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
#   chmod +x appimagetool && sudo mv appimagetool /usr/local/bin/
#
# Run from the project root: ./packaging/build_appimage.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

PYTHON="${PYTHON:-$APP_DIR/.venv/bin/python3}"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

ARCH="${ARCH:-x86_64}"
VERSION="$($PYTHON -c 'from _constants import VERSION_MAJOR, VERSION_MINOR, VERSION_REVISION; print(f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_REVISION}")')"
APPDIR="$APP_DIR/dist/AppDir"
OUTPUT="retromanager-${VERSION}-${ARCH}.AppImage"

echo "==> Building retromanager ${VERSION} AppImage"

# 1. PyInstaller bundle
echo "==> Running PyInstaller…"
"$PYTHON" -m PyInstaller packaging/retromanager.spec --distpath dist/pyinstaller --workpath build/pyinstaller --clean --noconfirm

# 2. Assemble AppDir
echo "==> Assembling AppDir…"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications"

# Copy the PyInstaller bundle into usr/bin/
cp -r dist/pyinstaller/retromanager/. "$APPDIR/usr/bin/"

# Icons
for size in 16 32 48 64 128 256 512; do
    mkdir -p "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps"
    cp "resources/icons/icon_${size}.png" \
       "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/retromanager.png"
done

# Symlink for appimagetool (needs top-level icon)
cp "resources/icons/icon_256.png" "$APPDIR/retromanager.png"

# Desktop file
cp "packaging/retromanager.desktop" "$APPDIR/retromanager.desktop"
# Patch Exec to the relative binary name used inside the AppImage
sed -i "s|Exec=.*|Exec=retromanager|" "$APPDIR/retromanager.desktop"

# AppRun wrapper
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HERE/usr/bin/retromanager" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# 3. Package with appimagetool
echo "==> Packaging AppImage…"
if ! command -v appimagetool &>/dev/null; then
    echo "ERROR: appimagetool not found. Install it from:"
    echo "  https://github.com/AppImage/AppImageKit/releases"
    exit 1
fi

ARCH="$ARCH" appimagetool "$APPDIR" "$OUTPUT"
echo "==> Done: $OUTPUT"
