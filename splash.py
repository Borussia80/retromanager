"""Splash screen shown during startup while the catalogue and UI are loaded."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from _constants import ICON_FILE, VERSION_MAJOR, VERSION_MINOR, VERSION_REVISION

_VERSION = f"v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_REVISION}"
_W, _H = 480, 280


def _build_pixmap() -> QPixmap:
    px = QPixmap(_W, _H)
    px.fill(QColor("#0d1221"))

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded border
    p.setPen(QColor("#1e2d4a"))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(1, 1, _W - 2, _H - 2, 12, 12)

    # App icon
    icon_src = QPixmap(ICON_FILE)
    if not icon_src.isNull():
        icon = icon_src.scaled(
            80, 80,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        p.drawPixmap((_W - icon.width()) // 2, 50, icon)

    # App name
    name_font = QFont()
    name_font.setPointSize(20)
    name_font.setBold(True)
    name_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
    p.setFont(name_font)
    p.setPen(QColor("#e8ecf5"))
    p.drawText(0, 152, _W, 32, Qt.AlignmentFlag.AlignHCenter, "RetroManager")

    # Version tag
    ver_font = QFont()
    ver_font.setPointSize(10)
    p.setFont(ver_font)
    p.setPen(QColor("#3a4a6b"))
    p.drawText(0, 184, _W, 22, Qt.AlignmentFlag.AlignHCenter, _VERSION)

    # Thin separator above the status area
    p.setPen(QColor("#1e2d4a"))
    p.drawLine(40, _H - 44, _W - 40, _H - 44)

    p.end()
    return px


class SplashScreen(QSplashScreen):
    def __init__(self) -> None:
        super().__init__(_build_pixmap(), Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

    def set_status(self, msg: str) -> None:
        """Update the status line and force a repaint before returning."""
        self.showMessage(
            msg,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            QColor("#6b7a99"),
        )
        QApplication.processEvents()
