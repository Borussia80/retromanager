"""Dialog showing RetroArch health details for a platform."""
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

from core.health import PlatformHealth

_SEVERITY_ICON = {"ok": "✅", "warning": "⚠️", "error": "❌"}
_SEVERITY_COLOR = {"ok": "#34c97e", "warning": "#f5a524", "error": "#e8453c"}


class HealthDialog(QDialog):
    def __init__(self, health: PlatformHealth, parent=None):
        super().__init__(parent)
        self._health = health
        self.setWindowTitle(f"Diagnóstico — {health.platform}")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background:#131929; border:1px solid #2e3a52; border-radius:10px; }
            QLabel  { background:transparent; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        # Header
        icon = _SEVERITY_ICON.get(self._health.severity, "❓")
        color = _SEVERITY_COLOR.get(self._health.severity, "#a9b4cc")
        title = QLabel(f"{icon}  {self._health.platform}")
        title.setStyleSheet(
            f"font-size:14px;font-weight:700;color:{color};"
        )
        lay.addWidget(title)

        lay.addWidget(self._divider())

        # Status rows
        self._row(lay, "RetroArch", self._health.retroarch_found)
        self._row(lay, f"Core  ({self._health.core_name})", self._health.core_installed)

        for bios in self._health.bios_required:
            present = bios in self._health.bios_found
            self._row(lay, f"BIOS  {bios}", present)

        if not self._health.bios_required and self._health.core_installed:
            ok = QLabel("Nenhuma BIOS necessária para esta plataforma.")
            ok.setStyleSheet("font-size:11px;color:#6b7a99;")
            lay.addWidget(ok)

        # Issues
        if self._health.issues:
            lay.addWidget(self._divider())
            for issue in self._health.issues:
                lbl = QLabel(f"• {issue}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet("font-size:11px;color:#a9b4cc;")
                lay.addWidget(lbl)

        lay.addWidget(self._divider())

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if not self._health.ready and self._health.bios_dir:
            bios_dir = self._health.bios_dir
            if bios_dir:
                btn_open = QPushButton("Abrir pasta de BIOS")
                btn_open.setStyleSheet(
                    "QPushButton{background:#1e2d4a;border:1px solid #2e3a52;"
                    "border-radius:6px;color:#a9b4cc;font-size:11px;padding:5px 12px;}"
                    "QPushButton:hover{background:#253550;color:#e8ecf5;}"
                )
                btn_open.clicked.connect(lambda: self._open_bios_folder(bios_dir))
                btn_row.addWidget(btn_open)

        btn_row.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(72)
        btn_ok.setStyleSheet(
            "QPushButton{background:#4f8ef7;border:none;border-radius:6px;"
            "color:#fff;font-size:12px;font-weight:600;padding:5px 0;}"
            "QPushButton:hover{background:#3a7ae0;}"
        )
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _row(self, layout: QVBoxLayout, label: str, ok: bool):
        row = QHBoxLayout()
        row.setSpacing(8)
        icon = QLabel("✅" if ok else "❌")
        icon.setFixedWidth(22)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size:12px;color:#e8ecf5;")
        row.addWidget(icon)
        row.addWidget(lbl, 1)
        layout.addLayout(row)

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setStyleSheet(
            "QFrame{border:none;background:#2e3a52;max-height:1px;margin:2px 0;}"
        )
        return f

    @staticmethod
    def _open_bios_folder(path: str):
        import os
        os.makedirs(path, exist_ok=True)
        subprocess.Popen(["xdg-open", path])
