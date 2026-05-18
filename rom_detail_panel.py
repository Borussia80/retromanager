from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox,
)
from PyQt6.QtGui import QCursor, QDesktopServices

from models import RomEntry
from _tools import Tools


class RomDetailPanel(QWidget):
    downloadRequested = pyqtSignal(str, str)   # platform, rom_name
    favoriteToggled   = pyqtSignal(str, str)   # platform, rom_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._platform = ""
        self._rom_name = ""
        self._rom_size = 0
        self._build_ui()
        self.clear()

    def _build_ui(self):
        self.setStyleSheet("background:#0f1117;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background:#0f1117; border:none; }")

        content = QWidget()
        content.setStyleSheet("background:#0f1117;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 20, 16, 20)
        cl.setSpacing(12)

        # Cover placeholder
        self._cover = QLabel("⊡")
        self._cover.setFixedSize(160, 120)
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setStyleSheet(
            "background:#1c2437;border-radius:8px;color:#3a4a6b;"
            "font-size:36px;border:none;"
        )
        cover_row = QHBoxLayout()
        cover_row.addStretch()
        cover_row.addWidget(self._cover)
        cover_row.addStretch()
        cl.addLayout(cover_row)

        # ROM title
        self._lbl_title = QLabel()
        self._lbl_title.setWordWrap(True)
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_title.setStyleSheet(
            "font-size:13px;font-weight:600;color:#e8ecf5;"
            "background:transparent;border:none;"
        )
        cl.addWidget(self._lbl_title)

        # Platform
        self._lbl_platform = QLabel()
        self._lbl_platform.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_platform.setStyleSheet(
            "font-size:10px;color:#6b7a99;background:transparent;border:none;"
        )
        cl.addWidget(self._lbl_platform)

        cl.addWidget(self._divider())

        # Metadata rows
        meta_wrap = QWidget()
        meta_wrap.setStyleSheet("background:transparent;")
        ml = QVBoxLayout(meta_wrap)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(5)
        self._lbl_size   = self._meta_row(ml, "Tamanho")
        self._lbl_format = self._meta_row(ml, "Formato")
        self._lbl_md5    = self._meta_row(ml, "MD5")
        self._lbl_crc32  = self._meta_row(ml, "CRC32")
        self._lbl_sha1   = self._meta_row(ml, "SHA1")
        cl.addWidget(meta_wrap)

        cl.addWidget(self._divider())

        # Download button
        self._btn_dl = QPushButton("Baixar")
        self._btn_dl.setFixedHeight(32)
        self._btn_dl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_dl.setStyleSheet("""
            QPushButton {
                background:#4f8ef7;border:none;border-radius:6px;
                color:#fff;font-size:12px;font-weight:600;
            }
            QPushButton:hover { background:#3a7ae0; }
            QPushButton:disabled { background:#252d40;color:#3a4a6b; }
        """)
        self._btn_dl.clicked.connect(self._on_download)
        cl.addWidget(self._btn_dl)

        # Favorite button
        self._btn_fav = QPushButton("★  Favoritar")
        self._btn_fav.setFixedHeight(28)
        self._btn_fav.setCheckable(True)
        self._btn_fav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_fav.setStyleSheet("""
            QPushButton {
                background:transparent;border:1px solid #2e3a52;border-radius:6px;
                color:#a9b4cc;font-size:11px;
            }
            QPushButton:hover { background:#1e2535;color:#e8ecf5; }
            QPushButton:checked {
                background:transparent;border-color:#f5a524;color:#f5a524;
            }
        """)
        self._btn_fav.clicked.connect(self._on_fav)
        cl.addWidget(self._btn_fav)

        # Archive.org link
        self._btn_archive = QPushButton("Abrir no archive.org →")
        self._btn_archive.setFixedHeight(26)
        self._btn_archive.setFlat(True)
        self._btn_archive.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_archive.setStyleSheet(
            "QPushButton { color:#4f8ef7;font-size:11px;background:transparent;"
            "border:none;text-align:left;padding-left:0; }"
            "QPushButton:hover { color:#7aaef9; }"
        )
        self._btn_archive.clicked.connect(self._on_archive)
        cl.addWidget(self._btn_archive)

        cl.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setStyleSheet(
            "QFrame { border:none;background:#2e3a52;max-height:1px;margin:4px 0; }"
        )
        return f

    def _meta_row(self, layout: QVBoxLayout, label: str) -> QLabel:
        row = QWidget()
        row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)
        key = QLabel(label)
        key.setFixedWidth(52)
        key.setStyleSheet("font-size:10px;color:#6b7a99;background:transparent;border:none;")
        val = QLabel("—")
        val.setStyleSheet("font-size:10px;color:#a9b4cc;background:transparent;border:none;")
        val.setWordWrap(True)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        rl.addWidget(key)
        rl.addWidget(val, 1)
        layout.addWidget(row)
        return val

    def show_rom(self, platform: str, rom_name: str, display_name: str,
                 rom_data: RomEntry, is_fav: bool, is_downloaded: bool = False):
        self._platform = platform
        self._rom_name = rom_name
        self._rom_size = rom_data.size

        self._lbl_title.setText(display_name)
        self._lbl_platform.setText(platform)
        self._lbl_size.setText(Tools.convertSizeToReadable(rom_data.size))
        self._lbl_format.setText((rom_data.format or "—").upper())
        self._lbl_md5.setText(rom_data.md5 or "—")
        self._lbl_crc32.setText((rom_data.crc32 or "—").upper())
        self._lbl_sha1.setText(rom_data.sha1 or "—")

        self._btn_fav.blockSignals(True)
        self._btn_fav.setChecked(is_fav)
        self._btn_fav.setText("★  Desfavoritar" if is_fav else "★  Favoritar")
        self._btn_fav.blockSignals(False)
        self._apply_download_state(is_downloaded)
        self._btn_fav.setEnabled(True)
        self._btn_archive.setVisible(True)

    def clear(self):
        self._platform = ""
        self._rom_name = ""
        self._rom_size = 0
        self._lbl_title.setText("Nenhuma ROM selecionada")
        self._lbl_platform.setText("")
        self._lbl_size.setText("—")
        self._lbl_format.setText("—")
        self._lbl_md5.setText("—")
        self._lbl_crc32.setText("—")
        self._lbl_sha1.setText("—")
        self._btn_fav.blockSignals(True)
        self._btn_fav.setChecked(False)
        self._btn_fav.setText("★  Favoritar")
        self._btn_fav.blockSignals(False)
        self._btn_dl.setEnabled(False)
        self._btn_fav.setEnabled(False)
        self._btn_archive.setVisible(False)

    def sync_fav(self, is_fav: bool):
        """Update favorite button without emitting a signal."""
        self._btn_fav.blockSignals(True)
        self._btn_fav.setChecked(is_fav)
        self._btn_fav.setText("★  Desfavoritar" if is_fav else "★  Favoritar")
        self._btn_fav.blockSignals(False)

    def sync_downloaded(self, is_downloaded: bool):
        """Update download button state after a download completes."""
        self._apply_download_state(is_downloaded)

    def _apply_download_state(self, is_downloaded: bool):
        if is_downloaded:
            self._btn_dl.setText("✓  Já baixado")
            self._btn_dl.setEnabled(False)
            self._btn_dl.setStyleSheet("""
                QPushButton {
                    background:#1a3a26;border:none;border-radius:6px;
                    color:#34c97e;font-size:12px;font-weight:600;
                }
                QPushButton:disabled { background:#1a3a26;color:#34c97e; }
            """)
        else:
            self._btn_dl.setText("Baixar")
            self._btn_dl.setEnabled(True)
            self._btn_dl.setStyleSheet("""
                QPushButton {
                    background:#4f8ef7;border:none;border-radius:6px;
                    color:#fff;font-size:12px;font-weight:600;
                }
                QPushButton:hover { background:#3a7ae0; }
                QPushButton:disabled { background:#252d40;color:#3a4a6b; }
            """)

    def _on_download(self):
        if not (self._platform and self._rom_name):
            return
        if self._rom_size and self._rom_size > 1_000_000_000:
            reply = QMessageBox.question(
                self,
                "Arquivo grande",
                f"Este arquivo tem {Tools.convertSizeToReadable(self._rom_size)}.\n"
                "Deseja continuar o download?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.downloadRequested.emit(self._platform, self._rom_name)

    def _on_fav(self):
        if self._platform and self._rom_name:
            self.favoriteToggled.emit(self._platform, self._rom_name)

    def _on_archive(self):
        query = self._rom_name.replace(" ", "+")
        QDesktopServices.openUrl(QUrl(f"https://archive.org/search?query={query}"))
