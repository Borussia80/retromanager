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


def _fetch_latest_tag(timeout_ms: int = 5_000) -> str | None:
    """Return the latest release tag string from GitHub, or None on failure."""
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
        tag = data[0].get("tag_name", "")
        if not isinstance(tag, str) or not _TAG_RE.match(tag):
            DebugHelper.print(DebugType.TYPE_WARNING,
                              f"Unexpected tag format: {tag!r}", "UPDATER")
            return None
        return tag
    finally:
        reply.deleteLater()


class UpdaterHelper:
    LASTEST_MAJOR    = VERSION_MAJOR
    LASTEST_MINOR    = VERSION_MINOR
    LASTEST_REVISION = VERSION_REVISION

    def __init__(self) -> None:
        pass

    def _fetchLatestRelease(self) -> None:
        tag = _fetch_latest_tag()
        if tag is None:
            return
        m = _TAG_RE.match(tag)
        if not m:
            return
        try:
            self.LASTEST_MAJOR    = int(m.group(1))
            self.LASTEST_MINOR    = int(m.group(2))
            self.LASTEST_REVISION = int(m.group(3) or 0)
        except (ValueError, TypeError) as e:
            DebugHelper.print(DebugType.TYPE_ERROR, str(e), "UPDATER")

    def updateAvailable(self) -> bool:
        self._fetchLatestRelease()
        if VERSION_MAJOR < self.LASTEST_MAJOR:
            DebugHelper.print(DebugType.TYPE_INFO, "Update available!", "UPDATER")
            return True
        if VERSION_MAJOR == self.LASTEST_MAJOR and VERSION_MINOR < self.LASTEST_MINOR:
            DebugHelper.print(DebugType.TYPE_INFO, "Update available!", "UPDATER")
            return True
        DebugHelper.print(DebugType.TYPE_INFO, "You have the latest version.", "UPDATER")
        return False

    def currentVersionString(self) -> str:
        return f"v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_REVISION}"

    def lastestVersionString(self) -> str:
        return f"v{self.LASTEST_MAJOR}.{self.LASTEST_MINOR}.{self.LASTEST_REVISION}"
