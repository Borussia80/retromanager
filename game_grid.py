from PyQt6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QSize,
    QRect, QSortFilterProxyModel, QThreadPool, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QFont, QBrush, QPen, QPainterPath,
)
from PyQt6.QtWidgets import (
    QListView, QStyledItemDelegate, QAbstractItemView, QStyle,
)

from platform_icons import PLATFORM_STYLE, parse_title_tags
from thumbnail_cache import ThumbnailFetcher, load_cached_path
from library_service import rom_matches_filters

CARD_W   = 150
CARD_H   = 220
THUMB_H  = 165
SPACING  =  10

# Custom roles
_ROLE_ROM      = Qt.ItemDataRole.UserRole       # str  — rom_name
_ROLE_DL       = Qt.ItemDataRole.UserRole + 1   # bool — downloaded
_ROLE_PX       = Qt.ItemDataRole.UserRole + 2   # QPixmap | None
_ROLE_PLATFORM = Qt.ItemDataRole.UserRole + 3   # str  — platform (same for all rows)


# ── Model ──────────────────────────────────────────────────────────────────────

class RomGridModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._platform: str = ""
        self._items: list[dict] = []   # {"name": str, "downloaded": bool, "pixmap": QPixmap|None}

    def load(self, platform: str, names: list[str], downloaded: set[str]):
        self.beginResetModel()
        self._platform = platform
        self._items = [
            {"name": n, "downloaded": n in downloaded, "pixmap": None}
            for n in names
        ]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        item = self._items[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, _ROLE_ROM):
            return item["name"]
        if role == _ROLE_DL:
            return item["downloaded"]
        if role == _ROLE_PX:
            return item["pixmap"]
        if role == _ROLE_PLATFORM:
            return self._platform
        return None

    def set_thumbnail(self, rom_name: str, pixmap: QPixmap):
        for i, item in enumerate(self._items):
            if item["name"] == rom_name:
                item["pixmap"] = pixmap
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [_ROLE_PX])
                return

    def platform(self) -> str:
        return self._platform


# ── Proxy filter ───────────────────────────────────────────────────────────────

class _RomFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._keywords: list[str] = []
        self._region: str | None = None

    def set_filter(self, keywords: list[str], region: str | None):
        self._keywords = [k.lower() for k in keywords]
        self._region = region
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        idx = self.sourceModel().index(source_row, 0, source_parent)
        name = idx.data(Qt.ItemDataRole.DisplayRole) or ""
        return rom_matches_filters(name, self._keywords, self._region)


# ── Delegate ───────────────────────────────────────────────────────────────────

class _GameCardDelegate(QStyledItemDelegate):
    _TITLE_H = CARD_H - THUMB_H

    def sizeHint(self, option, index) -> QSize:
        return QSize(CARD_W, CARD_H)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        painter.save()
        r: QRect = option.rect

        # Card background + border
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover    = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg     = QColor("#1e2d4a" if is_selected else "#1a2035" if is_hover else "#161b27")
        border = QColor("#4f8ef7" if (is_selected or is_hover) else "#2e3a52")

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(r.adjusted(1, 1, -1, -1), 6, 6)
        painter.fillPath(path, QBrush(bg))
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)

        # Thumbnail
        thumb_rect = QRect(r.x(), r.y(), r.width(), THUMB_H)
        px: QPixmap | None = index.data(_ROLE_PX)
        if px and not px.isNull():
            scaled = px.scaled(
                thumb_rect.width(), thumb_rect.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            tx = thumb_rect.x() + (thumb_rect.width() - scaled.width()) // 2
            ty = thumb_rect.y() + (thumb_rect.height() - scaled.height()) // 2
            painter.setClipRect(thumb_rect)
            painter.drawPixmap(tx, ty, scaled)
            painter.setClipping(False)
        else:
            self._draw_placeholder(painter, thumb_rect, index.data(_ROLE_PLATFORM) or "")

        # Downloaded badge
        if index.data(_ROLE_DL):
            bw, bh = 22, 22
            bx = r.right() - bw - 4
            by = r.top() + 4
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#1a3a26")))
            painter.drawEllipse(bx, by, bw, bh)
            f = QFont()
            f.setPointSize(10)
            f.setBold(True)
            painter.setFont(f)
            painter.setPen(QColor("#34c97e"))
            painter.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, "✓")

        # Title
        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        clean, _ = parse_title_tags(name)
        title_rect = QRect(r.x() + 4, r.y() + THUMB_H + 3, r.width() - 8, self._TITLE_H - 6)
        f2 = QFont()
        f2.setPointSize(9)
        painter.setFont(f2)
        painter.setPen(QColor("#a9b4cc"))
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter |
            Qt.TextFlag.TextWordWrap,
            clean,
        )

        painter.restore()

    @staticmethod
    def _draw_placeholder(painter: QPainter, rect: QRect, platform: str):
        style = PLATFORM_STYLE.get(platform, {"abbr": "?", "color": "#3d4f6e"})
        painter.fillRect(rect, QColor("#0f1117"))
        bg = QColor(style["color"])
        bg.setAlpha(22)
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        cx = rect.x() + rect.width() // 2
        cy = rect.y() + rect.height() // 2
        painter.drawEllipse(cx - 30, cy - 30, 60, 60)
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(style["color"]))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, style["abbr"])


# ── View ───────────────────────────────────────────────────────────────────────

class GameGridWidget(QListView):
    """Virtualised ROM grid — no per-card QWidget; delegate paints directly."""

    romDoubleClicked = pyqtSignal(str)   # rom_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = RomGridModel(self)
        self._proxy  = _RomFilterProxy(self)
        self._proxy.setSourceModel(self._source)
        self.setModel(self._proxy)
        self.setItemDelegate(_GameCardDelegate(self))

        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setSpacing(SPACING)
        self.setGridSize(QSize(CARD_W + SPACING, CARD_H + SPACING))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setMouseTracking(True)
        self.setStyleSheet("QListView { background:#0f1117; border:none; outline:none; }")

        self.doubleClicked.connect(self._on_double_clicked)
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)

    # ── Public API (same surface as old GameGridWidget) ────────────────────────

    def load(self, platform: str, rom_names: list[str], downloaded_set: set | None = None):
        self._source.load(platform, rom_names, downloaded_set or set())

        # Pre-load cached thumbnails, enqueue fetches for the rest
        for name in rom_names:
            if path := load_cached_path(platform, name):
                px = QPixmap(path)
                if not px.isNull():
                    self._source.set_thumbnail(name, px)
            else:
                fetcher = ThumbnailFetcher(platform, name)
                fetcher.signals.done.connect(self._on_thumbnail_done)
                self._pool.start(fetcher)

    def apply_filter(self, keywords: list[str], region: str | None):
        self._proxy.set_filter(keywords, region)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_double_clicked(self, proxy_index: QModelIndex):
        src = self._proxy.mapToSource(proxy_index)
        name = self._source.data(src, _ROLE_ROM)
        if name:
            self.romDoubleClicked.emit(name)

    def _on_thumbnail_done(self, platform: str, rom_name: str, path: str):
        if platform != self._source.platform():
            return
        px = QPixmap(path)
        if not px.isNull():
            self._source.set_thumbnail(rom_name, px)
