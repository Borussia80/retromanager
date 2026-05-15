import re
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QBrush, QPainter
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QStyledItemDelegate, QStyle, QApplication,
)


PLATFORM_STYLE: dict[str, dict] = {
    "Nintendo - NES":                    {"abbr": "NES", "color": "#e8453c"},
    "Nintendo - SNES":                   {"abbr": "SNS", "color": "#6a3f9b"},
    "Nintendo - 64":                     {"abbr": "N64", "color": "#e8453c"},
    "Nintendo - GameBoy":                {"abbr": "GB",  "color": "#8bac0f"},
    "Nintendo - GameBoy Color":          {"abbr": "GBC", "color": "#c8a000"},
    "Nintendo - GameBoy Advance":        {"abbr": "GBA", "color": "#8b3d8b"},
    "Nintendo - Famicom Disk":           {"abbr": "FDS", "color": "#1565c0"},
    "Sega - Megadrive / Genesis":        {"abbr": "GEN", "color": "#1976d2"},
    "Sega - Master System / Mark III":   {"abbr": "SMS", "color": "#e65100"},
    "Sega - Game Gear":                  {"abbr": "GG",  "color": "#2e7d32"},
    "Sega - 32X":                        {"abbr": "32X", "color": "#6a1b9a"},
    "Atari 2600":                        {"abbr": "A26", "color": "#c17900"},
    "Atari 5200":                        {"abbr": "A52", "color": "#b56a00"},
    "Atari 7800":                        {"abbr": "A78", "color": "#a05c00"},
    "NEC - PC Engine / TurboGrafx-16":   {"abbr": "PCE", "color": "#00838f"},
    "SNK - Neo Geo MVS":                 {"abbr": "NEO", "color": "#c62828"},
    "Arcade - MAME":                     {"abbr": "ARC", "color": "#4a148c"},
}

BADGE_TAGS: dict[str, tuple[str, str]] = {
    "Japan":        ("#c62828", "#ffffff"),
    "USA":          ("#1565c0", "#ffffff"),
    "Europe":       ("#2e7d32", "#ffffff"),
    "World":        ("#252d40", "#a9b4cc"),
    "Beta":         ("#1a1a2e", "#4f8ef7"),
    "Proto":        ("#1a1a2e", "#4f8ef7"),
    "Sample":       ("#1a2e1a", "#34c97e"),
    "Unl":          ("#4a3800", "#f5a623"),
    "Pirate":       ("#4a3800", "#f5a623"),
    "Aftermarket":  ("#2a1f3d", "#9b6ef3"),
    "Demo":         ("#1a1a2e", "#4f8ef7"),
}


def _default_style(name: str) -> dict:
    return {"abbr": name[:3].upper(), "color": "#3d4f6e"}


def _strip_manufacturer(name: str) -> str:
    """'Nintendo - GameBoy' → 'GameBoy'"""
    return name.split(" - ", 1)[-1] if " - " in name else name


def parse_title_tags(title: str) -> tuple[str, list[str]]:
    """'Super Mario World (USA) (Beta)' → ('Super Mario World', ['USA', 'Beta'])"""
    tags = re.findall(r'\(([^)]+)\)', title)
    clean = re.sub(r'\s*\([^)]+\)', '', title).strip()
    known = [t for t in tags if t in BADGE_TAGS]
    return clean, known


class PlatformIconWidget(QWidget):
    def __init__(self, abbr: str, color: str, parent=None):
        super().__init__(parent)
        self._abbr = abbr
        self._color = QColor(color)
        self.setFixedSize(32, 32)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 7, 7)
        p.setPen(QColor("#ffffff"))
        f = p.font()
        f.setPointSize(7 if len(self._abbr) > 2 else 8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._abbr)


class PlatformItemWidget(QWidget):
    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        style = PLATFORM_STYLE.get(name, _default_style(name))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        icon = PlatformIconWidget(style["abbr"], style["color"])
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        lbl_name = QLabel(_strip_manufacturer(name))
        lbl_name.setStyleSheet(
            "font-size:12px;font-weight:500;color:#e8ecf5;"
            "background:transparent;border:none;"
        )

        if count > 0:
            lbl_count = QLabel(f"{count:,} titles")
            lbl_count.setStyleSheet(
                "font-size:10px;color:#6b7a99;background:transparent;border:none;"
            )
        else:
            lbl_count = QLabel("Unavailable")
            lbl_count.setStyleSheet(
                "font-size:10px;color:#3d4f6e;background:transparent;border:none;"
            )

        text_col.addWidget(lbl_name)
        text_col.addWidget(lbl_count)
        layout.addLayout(text_col)
        layout.addStretch()

        if count == 0:
            self.setEnabled(False)
            lbl_name.setStyleSheet(
                "font-size:12px;font-weight:500;color:#3d4f6e;"
                "background:transparent;border:none;"
            )


class GameTitleDelegate(QStyledItemDelegate):
    _BADGE_FONT_PT = 8
    _BADGE_PAD_H = 5
    _BADGE_PAD_V = 2
    _BADGE_RADIUS = 3
    _ROW_H = 28

    def paint(self, painter, option, index):
        painter.save()

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1e2d4a"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#1e2535"))

        title = index.data(Qt.ItemDataRole.DisplayRole) or ""
        clean, tags = parse_title_tags(title)

        rect = option.rect.adjusted(8, 0, -8, 0)

        # Measure badges
        bf = QFont(option.font)
        bf.setPointSize(self._BADGE_FONT_PT)
        bf.setBold(True)
        bfm = QFontMetrics(bf)

        badge_rects: list[tuple[str, QRect]] = []
        x_right = rect.right()
        for tag in reversed(tags):
            if tag not in BADGE_TAGS:
                continue
            bw = bfm.horizontalAdvance(tag) + self._BADGE_PAD_H * 2
            bh = bfm.height() + self._BADGE_PAD_V * 2
            by = rect.top() + (rect.height() - bh) // 2
            r = QRect(x_right - bw, by, bw, bh)
            badge_rects.append((tag, r))
            x_right -= bw + 4

        # Title
        title_rect = QRect(rect.left(), rect.top(), x_right - rect.left() - 4, rect.height())
        painter.setFont(option.font)
        painter.setPen(QColor("#e8ecf5"))
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            clean,
        )

        # Badges
        painter.setFont(bf)
        for tag, r in badge_rects:
            bg, fg = BADGE_TAGS[tag]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(bg))
            painter.drawRoundedRect(r, self._BADGE_RADIUS, self._BADGE_RADIUS)
            painter.setPen(QColor(fg))
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, tag)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self._ROW_H)


class FormatBadgeDelegate(QStyledItemDelegate):
    """Renders the file format (zip, 7z) as a small monospaced pill badge."""
    _BADGE_RADIUS = 3
    _PAD_H = 8
    _PAD_V = 2

    def paint(self, painter, option, index):
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1e2d4a"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#1e2535"))

        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        if text:
            f = QFont(option.font)
            f.setFamily("monospace")
            f.setPointSize(9)
            fm = QFontMetrics(f)
            bw = fm.horizontalAdvance(text) + self._PAD_H * 2
            bh = fm.height() + self._PAD_V * 2
            bx = option.rect.center().x() - bw // 2
            by = option.rect.center().y() - bh // 2
            r = QRect(bx, by, bw, bh)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1e2535"))
            painter.drawRoundedRect(r, self._BADGE_RADIUS, self._BADGE_RADIUS)
            painter.setFont(f)
            painter.setPen(QColor("#6b7a99"))
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 28)
