#!/usr/bin/env python3
"""Generate the retromanager app icon — Atari-style M logo."""
import sys, os
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPixmap, QPainterPath, QLinearGradient
from PyQt6.QtWidgets import QApplication


def make_icon(size: int = 256) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    S = size / 64  # scale: design is on 64×64 grid

    def r(v): return v * S  # scale a value

    # ── Background: dark rounded square ───────────────────────────────────
    bg = QPainterPath()
    bg.addRoundedRect(QRectF(0, 0, size, size), r(12), r(12))
    p.fillPath(bg, QColor("#0f1117"))

    # ── Atari-M shape ─────────────────────────────────────────────────────
    # The "fuji" Atari logo has three vertical bars merging at the bottom.
    # We replace the three bars with four M-strokes + a common base:
    #   • Two tall outer bars  (left and right)
    #   • Two inner diagonals  (leaning inward toward a central valley)
    #   • One wide base bar    (connects everything — gives the Atari character)
    #
    # Grid reference (64 × 64, pad = 5):
    #   Outer bars:  x = 5..17  and  47..59,  y = 7..57
    #   Inner tops:  x = 19..29 and  35..45,  y = 7
    #   Valley:      x = 26..38,               y = 38
    #   Base:        x = 5..59,                y = 47..57

    color = QColor("#f5a623")   # amber — classic Atari orange

    path = QPainterPath()

    # Left outer bar (rounded cap at top)
    path.addRoundedRect(QRectF(r(5), r(7), r(12), r(50)), r(4), r(4))

    # Right outer bar (rounded cap at top)
    path.addRoundedRect(QRectF(r(47), r(7), r(12), r(50)), r(4), r(4))

    # Base bar (connects everything at the bottom)
    path.addRoundedRect(QRectF(r(5), r(47), r(54), r(10)), r(3), r(3))

    # Left inner diagonal: top=(19..29, y=7) → valley=(26..38, y=38)
    ld = QPainterPath()
    ld.moveTo(r(19), r(7))
    ld.lineTo(r(29), r(7))
    ld.lineTo(r(38), r(38))
    ld.lineTo(r(26), r(38))
    ld.closeSubpath()
    path.addPath(ld)

    # Right inner diagonal: top=(35..45, y=7) → valley=(26..38, y=38)
    rd = QPainterPath()
    rd.moveTo(r(35), r(7))
    rd.lineTo(r(45), r(7))
    rd.lineTo(r(38), r(38))
    rd.lineTo(r(26), r(38))
    rd.closeSubpath()
    path.addPath(rd)

    # Fill with amber gradient (top: bright, bottom: slightly darker)
    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0.0, QColor("#ffc040"))   # bright top
    grad.setColorAt(1.0, QColor("#d4810a"))   # darker bottom

    from PyQt6.QtGui import QBrush
    p.fillPath(path, QBrush(grad))

    p.end()
    return px


if __name__ == "__main__":
    app = QApplication(sys.argv)
    out = os.path.join(os.path.dirname(__file__), "icon.png")
    make_icon(256).save(out)
    print(f"Saved: {out}")
