from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThreadPool
from PyQt6.QtGui import QColor, QPainter, QPixmap, QFont, QBrush
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QGridLayout, QVBoxLayout, QLabel, QFrame,
)

from platform_icons import PLATFORM_STYLE, parse_title_tags
from thumbnail_cache import ThumbnailFetcher, load_cached_path

CARD_W = 140
THUMB_W = 140
THUMB_H = 160
MAX_GRID_ITEMS = 500


class GameCardWidget(QFrame):
    doubleClicked = pyqtSignal(str)  # rom_name

    def __init__(self, rom_name: str, platform: str, parent=None):
        super().__init__(parent)
        self._rom_name = rom_name
        self._platform = platform
        clean, _ = parse_title_tags(rom_name)

        self.setFixedWidth(CARD_W)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            GameCardWidget {
                background: #161b27;
                border: 1px solid #2e3a52;
                border-radius: 6px;
            }
            GameCardWidget:hover {
                border-color: #4f8ef7;
                background: #1a2035;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(4)

        self._thumb = QLabel()
        self._thumb.setFixedSize(THUMB_W, THUMB_H)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            "background:#0f1117;border-radius:6px 6px 0 0;border:none;"
        )
        self._draw_placeholder()
        lay.addWidget(self._thumb)

        lbl = QLabel(clean)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        lbl.setStyleSheet(
            "font-size:10px;color:#a9b4cc;background:transparent;"
            "border:none;padding:0 4px;"
        )
        lbl.setFixedHeight(36)
        lay.addWidget(lbl)

    def _draw_placeholder(self):
        style = PLATFORM_STYLE.get(self._platform, {"abbr": "?", "color": "#3d4f6e"})
        px = QPixmap(THUMB_W, THUMB_H)
        px.fill(QColor("#0f1117"))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(style["color"])
        bg.setAlpha(22)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        cx, cy = THUMB_W // 2, THUMB_H // 2
        p.drawEllipse(cx - 30, cy - 30, 60, 60)
        p.setPen(QColor(style["color"]))
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        p.setFont(f)
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, style["abbr"])
        p.end()
        self._thumb.setPixmap(px)

    def set_thumbnail(self, path: str):
        src = QPixmap(path)
        if src.isNull():
            return
        scaled = src.scaled(
            THUMB_W, THUMB_H,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        canvas = QPixmap(THUMB_W, THUMB_H)
        canvas.fill(QColor("#0f1117"))
        p = QPainter(canvas)
        p.drawPixmap(
            (THUMB_W - scaled.width()) // 2,
            (THUMB_H - scaled.height()) // 2,
            scaled,
        )
        p.end()
        self._thumb.setPixmap(canvas)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self._rom_name)
        super().mouseDoubleClickEvent(event)


class GameGridWidget(QScrollArea):
    romDoubleClicked = pyqtSignal(str)

    _SPACING = 12
    _MARGIN = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea{border:none;background:#0f1117;}")

        self._container = QWidget()
        self._container.setStyleSheet("background:#0f1117;")
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(
            self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN
        )
        self._grid.setSpacing(self._SPACING)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self._cards: dict[str, GameCardWidget] = {}
        self._platform = ""
        self._cols = 4

        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)

        self._reflow_timer = QTimer(self)
        self._reflow_timer.setSingleShot(True)
        self._reflow_timer.setInterval(120)
        self._reflow_timer.timeout.connect(self._reflow)

    # ── Public API ──────────────────────────────────────────

    def load(self, platform: str, rom_names: list[str]):
        self._platform = platform

        while self._grid.count():
            item = self._grid.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        self._cards.clear()

        subset = rom_names[:MAX_GRID_ITEMS]
        cols = self._cols

        for i, name in enumerate(subset):
            card = GameCardWidget(name, platform)
            card.doubleClicked.connect(self.romDoubleClicked)
            self._grid.addWidget(card, i // cols, i % cols)
            self._cards[name] = card
            if path := load_cached_path(platform, name):
                card.set_thumbnail(path)

        if len(rom_names) > MAX_GRID_ITEMS:
            note = QLabel(
                f"Mostrando {MAX_GRID_ITEMS:,} de {len(rom_names):,} ROMs — "
                "use a busca para filtrar."
            )
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            note.setStyleSheet(
                "color:#3d4f6e;font-size:11px;padding:8px;"
                "background:transparent;border:none;"
            )
            self._grid.addWidget(note, len(subset) // cols + 1, 0, 1, cols)

        # Fetch thumbnails that aren't cached yet
        for name in subset:
            if not load_cached_path(platform, name):
                fetcher = ThumbnailFetcher(platform, name)
                fetcher.signals.done.connect(self._on_done)
                self._pool.start(fetcher)

    def apply_filter(self, keywords: list[str], region: str | None):
        for name, card in self._cards.items():
            target = name.lower()
            show = True
            if region and f"({region.lower()})" not in target:
                show = False
            elif keywords and not all(kw in target for kw in keywords):
                show = False
            card.setVisible(show)

    # ── Internal ────────────────────────────────────────────

    def _on_done(self, platform: str, rom_name: str, path: str):
        if platform != self._platform:
            return
        if card := self._cards.get(rom_name):
            card.set_thumbnail(path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_timer.start()

    def _reflow(self):
        if not self._cards:
            return
        available = self.viewport().width() - self._MARGIN * 2
        new_cols = max(2, available // (CARD_W + self._SPACING))
        if new_cols == self._cols:
            return
        self._cols = new_cols
        names = list(self._cards.keys())
        for i, name in enumerate(names):
            self._grid.addWidget(self._cards[name], i // new_cols, i % new_cols)
