from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


class DownloadErrorDialog(QDialog):
    def __init__(self, rom_name: str, platform: str, reason: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download failed")
        self.setModal(True)
        self.setFixedWidth(440)
        self.setStyleSheet("""
            QDialog {
                background: #1a1f2e;
            }
            QLabel { background: transparent; border: none; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(14)

        # Header row: circle icon + title
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        icon = QLabel("✕")
        icon.setFixedSize(38, 38)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("""
            background: #3d1a1e;
            color: #f04a5a;
            border-radius: 19px;
            font-size: 15px;
            font-weight: bold;
        """)

        lbl_title = QLabel("Download failed")
        lbl_title.setStyleSheet("font-size:16px;font-weight:600;color:#e8ecf5;")

        hdr.addWidget(icon)
        hdr.addWidget(lbl_title, 1)
        lay.addLayout(hdr)

        # ROM name block
        lbl_rom = QLabel(f"[{platform}]  {rom_name}")
        lbl_rom.setStyleSheet(
            "background:#252d40;border-radius:6px;padding:9px 12px;"
            "font-size:12px;color:#a9b4cc;font-family:monospace;"
        )
        lbl_rom.setWordWrap(True)
        lay.addWidget(lbl_rom)

        # Error reason
        lbl_reason = QLabel(reason)
        lbl_reason.setStyleSheet("font-size:12px;color:#f04a5a;")
        lbl_reason.setWordWrap(True)
        lay.addWidget(lbl_reason)

        # Hint
        lbl_hint = QLabel("The item remains in the queue — you can retry it.")
        lbl_hint.setStyleSheet("font-size:11px;color:#6b7a99;")
        lbl_hint.setWordWrap(True)
        lay.addWidget(lbl_hint)

        lay.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_retry = QPushButton("↺  Retry")
        self.btn_retry.setStyleSheet("""
            QPushButton {
                background:#4f8ef7;border:none;border-radius:6px;
                padding:8px 20px;color:#fff;font-weight:600;font-size:13px;
            }
            QPushButton:hover { background:#3a6fd4; }
            QPushButton:pressed { background:#2e5ab0; }
        """)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background:#252d40;border:1px solid #2e3a52;border-radius:6px;
                padding:8px 20px;color:#a9b4cc;font-size:13px;
            }
            QPushButton:hover { background:#2e3a52;color:#e8ecf5; }
            QPushButton:pressed { background:#1a2030; }
        """)

        self.btn_retry.clicked.connect(self.accept)
        self.btn_ok.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_retry)
        btn_row.addWidget(self.btn_ok)
        lay.addLayout(btn_row)
