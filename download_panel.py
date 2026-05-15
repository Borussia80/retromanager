from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QPushButton,
)


def _fmt_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1_048_576:
        return f"{b / 1024:.0f} KB"
    return f"{b / 1_048_576:.1f} MB"


class DownloadItemWidget(QWidget):
    def __init__(self, rom_name: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QWidget { border-bottom: 1px solid #2e3a52; background: transparent; }"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        self.lbl_name = QLabel(rom_name)
        self.lbl_name.setStyleSheet("font-size:11px;color:#e8ecf5;border:none;")
        self.lbl_name.setWordWrap(False)

        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setValue(0)
        self.bar.setFixedHeight(4)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet("""
            QProgressBar { background:#252d40; border-radius:2px; border:none; }
            QProgressBar::chunk { background:#4f8ef7; border-radius:2px; }
        """)

        self.lbl_meta = QLabel("Queued")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#6b7a99;border:none;")

        lay.addWidget(self.lbl_name)
        lay.addWidget(self.bar)
        lay.addWidget(self.lbl_meta)

    def set_downloading(self):
        self.lbl_meta.setText("Starting…")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#4f8ef7;border:none;")

    def set_progress(self, bytes_done: int, total_bytes: int, speed: float):
        if total_bytes > 0:
            self.bar.setValue(int(bytes_done / total_bytes * 1000))
            pct = int(bytes_done / total_bytes * 100)
            self.lbl_meta.setText(
                f"{pct}%  ·  {_fmt_bytes(bytes_done)} / {_fmt_bytes(total_bytes)}"
                f"  ·  {_fmt_bytes(int(speed))}/s"
            )
        else:
            self.lbl_meta.setText(f"{_fmt_bytes(bytes_done)}  ·  {_fmt_bytes(int(speed))}/s")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#4f8ef7;border:none;")

    def set_complete(self):
        self.bar.setValue(1000)
        self.bar.setStyleSheet("""
            QProgressBar { background:#252d40; border-radius:2px; border:none; }
            QProgressBar::chunk { background:#34c97e; border-radius:2px; }
        """)
        self.lbl_meta.setText("Done")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#34c97e;border:none;")

    def set_failed(self, error: str = ""):
        self.bar.setStyleSheet("""
            QProgressBar { background:#252d40; border-radius:2px; border:none; }
            QProgressBar::chunk { background:#e8453c; border-radius:2px; }
        """)
        self.lbl_meta.setText(f"Failed  ·  {error[:40]}" if error else "Failed")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#e8453c;border:none;")

    def set_cancelled(self):
        self.lbl_meta.setText("Cancelled")
        self.lbl_meta.setStyleSheet("font-size:10px;color:#6b7a99;border:none;")


class DownloadQueuePanel(QWidget):
    downloadRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)
        self.setStyleSheet(
            "QWidget#DownloadQueuePanel { background:#161b27; border-left:1px solid #2e3a52; }"
        )
        self.setObjectName("DownloadQueuePanel")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(40)
        hdr.setStyleSheet(
            "background:#161b27;border-bottom:1px solid #2e3a52;"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 0, 12, 0)

        lbl_title = QLabel("Downloads")
        lbl_title.setStyleSheet(
            "font-size:12px;font-weight:600;color:#a9b4cc;background:transparent;border:none;"
        )

        self._badge = QLabel("0")
        self._badge.setStyleSheet(
            "background:#252d40;color:#6b7a99;font-size:10px;"
            "padding:1px 7px;border-radius:9px;"
        )

        self._btn_start = QPushButton("▶")
        self._btn_start.setFixedSize(24, 24)
        self._btn_start.setToolTip("Start downloading queued items")
        self._btn_start.setStyleSheet("""
            QPushButton {
                background:#4f8ef7;color:#fff;border:none;
                border-radius:5px;font-size:11px;font-weight:600;
            }
            QPushButton:hover { background:#3a6fd4; }
            QPushButton:pressed { background:#2e5ab0; }
            QPushButton:disabled { background:#1e2535;color:#3d4f6e; }
        """)
        self._btn_start.setEnabled(False)
        self._btn_start.clicked.connect(self.downloadRequested)

        hdr_lay.addWidget(lbl_title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(self._badge)
        hdr_lay.addSpacing(6)
        hdr_lay.addWidget(self._btn_start)
        root.addWidget(hdr)

        # Empty state
        self._empty_lbl = QLabel("No downloads yet.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color:#3d4f6e;font-size:12px;padding:20px;background:transparent;border:none;")

        # Scroll area for items
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border:none; background:#161b27; }")

        self._inner = QWidget()
        self._inner.setStyleSheet("background:#161b27;")
        self._inner_lay = QVBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(0, 0, 0, 0)
        self._inner_lay.setSpacing(0)
        self._inner_lay.addWidget(self._empty_lbl)
        self._inner_lay.addStretch()

        self._scroll.setWidget(self._inner)
        root.addWidget(self._scroll)

        self._items: dict[str, DownloadItemWidget] = {}

    def _refresh_badge(self):
        n = len(self._items)
        self._badge.setText(str(n))
        if n > 0:
            self._badge.setStyleSheet(
                "background:#4f8ef7;color:#fff;font-size:10px;"
                "padding:1px 7px;border-radius:9px;"
            )
            self._empty_lbl.hide()
        else:
            self._badge.setStyleSheet(
                "background:#252d40;color:#6b7a99;font-size:10px;"
                "padding:1px 7px;border-radius:9px;"
            )
            self._empty_lbl.show()

    def set_downloading(self, active: bool):
        """Disable the Start button while a download is in progress."""
        self._btn_start.setEnabled(not active)

    def add_item(self, rom_name: str):
        if rom_name in self._items:
            return
        widget = DownloadItemWidget(rom_name)
        # insert before the stretch
        self._inner_lay.insertWidget(self._inner_lay.count() - 1, widget)
        self._items[rom_name] = widget
        self._refresh_badge()

    def start_item(self, rom_name: str):
        if rom_name in self._items:
            self._items[rom_name].set_downloading()

    def update_progress(self, rom_name: str, bytes_done: int, total_bytes: int, speed: float):
        if rom_name in self._items:
            self._items[rom_name].set_progress(bytes_done, total_bytes, speed)

    def complete_item(self, rom_name: str):
        if rom_name in self._items:
            self._items[rom_name].set_complete()

    def fail_item(self, rom_name: str, error: str = ""):
        if rom_name in self._items:
            self._items[rom_name].set_failed(error)

    def cancel_item(self, rom_name: str):
        if rom_name in self._items:
            self._items[rom_name].set_cancelled()

    def clear(self):
        for w in self._items.values():
            w.deleteLater()
        self._items.clear()
        self._refresh_badge()
