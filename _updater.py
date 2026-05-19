import json
import re

from PyQt6.QtCore import QEventLoop, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from _constants import VERSION_MAJOR, VERSION_MINOR, VERSION_REVISION
from _debug import DebugHelper, DebugType

# Only release data from this exact endpoint is trusted.
_TRUSTED_API = "https://api.github.com/repos/Borussia80/retromanager/releases"

# Expected tag format: v<major>.<minor> or v<major>.<minor>.<patch>
_TAG_RE = re.compile(r'^v?(\d+)\.(\d+)(?:\.(\d+))?')


def _fetch_latest_release(timeout_ms: int = 5_000) -> tuple[str, str] | None:
    """Return (tag, appimage_url) for the latest release, or None on failure.

    appimage_url may be empty if the release has no .AppImage asset.
    """
    manager = QNetworkAccessManager()
    loop = QEventLoop()

    request = QNetworkRequest(QUrl(_TRUSTED_API))
    request.setRawHeader(b"Accept", b"application/vnd.github+json")
    request.setTransferTimeout(timeout_ms)

    reply = manager.get(request)
    reply.finished.connect(loop.quit)
    loop.exec()

    try:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            DebugHelper.print(DebugType.TYPE_ERROR,
                              f"Network error: {reply.errorString()}", "UPDATER")
            return None
        raw = bytes(reply.readAll()).decode("utf-8", errors="replace")
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            DebugHelper.print(DebugType.TYPE_WARNING, "Empty release list", "UPDATER")
            return None
        release = data[0]
        tag = release.get("tag_name", "")
        if not isinstance(tag, str) or not _TAG_RE.match(tag):
            DebugHelper.print(DebugType.TYPE_WARNING,
                              f"Unexpected tag format: {tag!r}", "UPDATER")
            return None
        appimage_url = ""
        for asset in release.get("assets", []):
            if asset.get("name", "").endswith(".AppImage"):
                appimage_url = asset.get("browser_download_url", "")
                break
        return tag, appimage_url
    finally:
        reply.deleteLater()


class UpdaterHelper:
    LATEST_MAJOR    = VERSION_MAJOR
    LATEST_MINOR    = VERSION_MINOR
    LATEST_REVISION = VERSION_REVISION
    _latest_appimage_url: str = ""

    def __init__(self) -> None:
        pass

    def _fetchLatestRelease(self) -> None:
        result = _fetch_latest_release()
        if result is None:
            return
        tag, self._latest_appimage_url = result
        m = _TAG_RE.match(tag)
        if not m:
            return
        try:
            self.LATEST_MAJOR    = int(m.group(1))
            self.LATEST_MINOR    = int(m.group(2))
            self.LATEST_REVISION = int(m.group(3) or 0)
        except (ValueError, TypeError) as e:
            DebugHelper.print(DebugType.TYPE_ERROR, str(e), "UPDATER")

    def updateAvailable(self) -> bool:
        self._fetchLatestRelease()
        cur = (VERSION_MAJOR, VERSION_MINOR, VERSION_REVISION)
        lat = (self.LATEST_MAJOR, self.LATEST_MINOR, self.LATEST_REVISION)
        if lat > cur:
            DebugHelper.print(DebugType.TYPE_INFO, "Update available!", "UPDATER")
            return True
        DebugHelper.print(DebugType.TYPE_INFO, "You have the latest version.", "UPDATER")
        return False

    def latestAppImageUrl(self) -> str:
        return self._latest_appimage_url

    def currentVersionString(self) -> str:
        return f"v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_REVISION}"

    def latestVersionString(self) -> str:
        return f"v{self.LATEST_MAJOR}.{self.LATEST_MINOR}.{self.LATEST_REVISION}"
