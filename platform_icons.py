import logging
import os
import re
import time

from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QBrush, QPainter
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
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


_log = logging.getLogger("retromanager.delegate")
_PERF_PROFILE = os.environ.get("DEBUG", "0") == "4"


def _default_style(name: str) -> dict:
    return {"abbr": name[:3].upper(), "color": "#3d4f6e"}


def _strip_manufacturer(name: str) -> str:
    """'Nintendo - GameBoy' → 'GameBoy'"""
    return name.split(" - ", 1)[-1] if " - " in name else name


def fmt_count(n: int) -> str:
    """Human-readable count for status bar and tooltips (not for sidebar items)."""
    if n == 0:
        return "vazio"
    if n == 1:
        return "1 item"
    return f"{n:,} itens".replace(",", ".")


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
    _STYLE_COUNT_IDLE = "font-size:10px;color:#6b7a99;background:transparent;border:none;"
    _STYLE_COUNT_SEL  = "font-size:10px;color:rgba(232,236,245,180);background:transparent;border:none;"
    _STYLE_COUNT_OFF  = "font-size:10px;color:#3d4f6e;background:transparent;border:none;"

    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        style = PLATFORM_STYLE.get(name, _default_style(name))
        self._full_name = _strip_manufacturer(name)
        self._available = count > 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        icon = PlatformIconWidget(style["abbr"], style["color"])
        layout.addWidget(icon)

        self._lbl_name = QLabel(self._full_name)
        self._lbl_name.setTextFormat(Qt.TextFormat.PlainText)
        self._lbl_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._lbl_name.setMinimumWidth(0)
        self._lbl_name.setToolTip(self._full_name)

        if self._available:
            self._lbl_name.setStyleSheet(
                "font-size:12px;font-weight:500;color:#e8ecf5;"
                "background:transparent;border:none;"
            )
            # TODO(audit): F·02b — separar estados "indisponível" e "vazio".
            # #3d4f6e (cor "Indisponível") provavelmente falha WCAG AA — reavaliar.
            count_txt = f"{count:,}".replace(",", ".")
            count_style = self._STYLE_COUNT_IDLE
        else:
            self._lbl_name.setStyleSheet(
                "font-size:12px;font-weight:500;color:#3d4f6e;"
                "background:transparent;border:none;"
            )
            count_txt = "Indisponível"
            count_style = self._STYLE_COUNT_OFF
            self.setEnabled(False)

        self._lbl_count = QLabel(count_txt)
        self._lbl_count.setStyleSheet(count_style)

        layout.addWidget(self._lbl_name)
        layout.addWidget(self._lbl_count)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_name()

    def _update_elided_name(self):
        fm = self._lbl_name.fontMetrics()
        count_w = self._lbl_count.sizeHint().width()
        # icon(32) + left-margin(10) + spacing(10) + [name] + spacing(10) + count + right-margin(10)
        available = self.width() - 72 - count_w
        elided = fm.elidedText(self._full_name, Qt.TextElideMode.ElideRight, max(available, 20))
        self._lbl_name.setText(elided)

    def set_selected(self, selected: bool):
        if not self._available:
            return
        self._lbl_count.setStyleSheet(
            self._STYLE_COUNT_SEL if selected else self._STYLE_COUNT_IDLE
        )


class GameTitleDelegate(QStyledItemDelegate):
    _BADGE_FONT_PT = 8
    _BADGE_PAD_H = 5
    _BADGE_PAD_V = 2
    _BADGE_RADIUS = 3
    _ROW_H = 28

    def paint(self, painter, option, index):
        if _PERF_PROFILE:
            _t0 = time.perf_counter()

        painter.save()

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#1e2d4a"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#1e2535"))

        title = index.data(Qt.ItemDataRole.DisplayRole) or ""
        downloaded  = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        is_favorite = bool(index.data(Qt.ItemDataRole.UserRole + 2))
        clean, tags = parse_title_tags(title)

        rect = option.rect.adjusted(8, 0, -8, 0)

        # Measure badges
        bf = QFont(option.font)
        bf.setPointSize(self._BADGE_FONT_PT)
        bf.setBold(True)
        bfm = QFontMetrics(bf)

        x_right = rect.right()

        # Checkmark measured first — occupies the rightmost slot
        chk_text = "✓"
        chk_r: QRect | None = None
        if downloaded:
            chk_w = bfm.horizontalAdvance(chk_text) + self._BADGE_PAD_H * 2
            chk_h = bfm.height() + self._BADGE_PAD_V * 2
            chk_y = rect.top() + (rect.height() - chk_h) // 2
            chk_r = QRect(x_right - chk_w, chk_y, chk_w, chk_h)
            x_right -= chk_w + 4

        badge_rects: list[tuple[str, QRect]] = []
        for tag in reversed(tags):
            if tag not in BADGE_TAGS:
                continue
            bw = bfm.horizontalAdvance(tag) + self._BADGE_PAD_H * 2
            bh = bfm.height() + self._BADGE_PAD_V * 2
            by = rect.top() + (rect.height() - bh) // 2
            r = QRect(x_right - bw, by, bw, bh)
            badge_rects.append((tag, r))
            x_right -= bw + 4

        # Star indicator on the left edge
        x_left = rect.left()
        if is_favorite:
            star_w = bfm.horizontalAdvance("★") + 4
            star_rect = QRect(x_left, rect.top(), star_w, rect.height())
            painter.setFont(bf)
            painter.setPen(QColor("#ffc040"))
            painter.drawText(
                star_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                "★",
            )
            x_left += star_w + 2

        # Title
        title_rect = QRect(x_left, rect.top(), x_right - x_left - 4, rect.height())
        painter.setFont(option.font)
        painter.setPen(QColor("#34c97e") if downloaded else QColor("#e8ecf5"))
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            clean,
        )

        # Checkmark badge
        if chk_r is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1a3a26"))
            painter.drawRoundedRect(chk_r, self._BADGE_RADIUS, self._BADGE_RADIUS)
            painter.setFont(bf)
            painter.setPen(QColor("#34c97e"))
            painter.drawText(chk_r, Qt.AlignmentFlag.AlignCenter, chk_text)

        # Region tag badges
        painter.setFont(bf)
        for tag, r in badge_rects:
            bg, fg = BADGE_TAGS[tag]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(bg))
            painter.drawRoundedRect(r, self._BADGE_RADIUS, self._BADGE_RADIUS)
            painter.setPen(QColor(fg))
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, tag)

        painter.restore()

        if _PERF_PROFILE:
            elapsed_us = (time.perf_counter() - _t0) * 1_000_000
            if elapsed_us > 500:
                _log.debug("GameTitleDelegate.paint slow: row=%d  %.0f µs",
                           index.row(), elapsed_us)

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self._ROW_H)


class FavoritesItemWidget(QWidget):
    _STYLE_COUNT_IDLE = "font-size:10px;color:#6b7a99;background:transparent;border:none;"
    _STYLE_COUNT_SEL  = "font-size:10px;color:rgba(232,236,245,180);background:transparent;border:none;"

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        icon = PlatformIconWidget("★", "#b8860b")
        layout.addWidget(icon)

        lbl_name = QLabel("Favoritos")
        lbl_name.setTextFormat(Qt.TextFormat.PlainText)
        lbl_name.setStyleSheet(
            "font-size:12px;font-weight:500;color:#e8ecf5;"
            "background:transparent;border:none;"
        )

        self._lbl_count = QLabel(self._fmt_num(count))
        self._lbl_count.setStyleSheet(self._STYLE_COUNT_IDLE)

        layout.addWidget(lbl_name, 1)
        layout.addWidget(self._lbl_count)

    def update_count(self, count: int):
        self._lbl_count.setText(self._fmt_num(count))

    def set_selected(self, selected: bool):
        self._lbl_count.setStyleSheet(
            self._STYLE_COUNT_SEL if selected else self._STYLE_COUNT_IDLE
        )

    @staticmethod
    def _fmt_num(n: int) -> str:
        return f"{n:,}".replace(",", ".") if n else ""


class HistoryItemWidget(QWidget):
    _STYLE_COUNT_IDLE = "font-size:10px;color:#6b7a99;background:transparent;border:none;"
    _STYLE_COUNT_SEL  = "font-size:10px;color:rgba(232,236,245,180);background:transparent;border:none;"

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        icon = PlatformIconWidget("◷", "#1565c0")
        layout.addWidget(icon)

        lbl_name = QLabel("Recentes")
        lbl_name.setTextFormat(Qt.TextFormat.PlainText)
        lbl_name.setStyleSheet(
            "font-size:12px;font-weight:500;color:#e8ecf5;"
            "background:transparent;border:none;"
        )

        self._lbl_count = QLabel(self._fmt_num(count))
        self._lbl_count.setStyleSheet(self._STYLE_COUNT_IDLE)

        layout.addWidget(lbl_name, 1)
        layout.addWidget(self._lbl_count)

    def update_count(self, count: int):
        self._lbl_count.setText(self._fmt_num(count))

    def set_selected(self, selected: bool):
        self._lbl_count.setStyleSheet(
            self._STYLE_COUNT_SEL if selected else self._STYLE_COUNT_IDLE
        )

    @staticmethod
    def _fmt_num(n: int) -> str:
        return f"{n:,}".replace(",", ".") if n else ""


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
