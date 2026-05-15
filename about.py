from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)

from _constants import ABOUT_LOGO


class About(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o Retromanager")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 24)
        lay.setSpacing(16)

        # Header: wordmark (marca pixel-art + "RETROMANAGER") + subtítulo
        hdr = QVBoxLayout()
        hdr.setSpacing(8)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = QPixmap(ABOUT_LOGO)
        if not px.isNull():
            # Pixel-art: FastTransformation mantém nitidez; exibir no tamanho natural
            logo.setPixmap(px)
        logo.setStyleSheet("background:transparent;border:none;")

        lbl_sub = QLabel("Gerenciador de biblioteca de jogos retro")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;border:none;")

        hdr.addWidget(logo)
        hdr.addWidget(lbl_sub)
        lay.addLayout(hdr)

        # Divider
        div = QLabel()
        div.setFixedHeight(1)
        div.setStyleSheet("background:#2e3a52;border:none;")
        lay.addWidget(div)

        # Description
        desc = QLabel(
            "Navegue e baixe ROMs de jogos retro diretamente do "
            "<a href='https://archive.org' style='color:#4f8ef7;'>archive.org</a>. "
            "Suporta 17+ plataformas, incluindo NES, SNES, N64, Game Boy, Sega, "
            "Atari, PC Engine, Neo Geo MVS e arcade MAME."
        )
        desc.setWordWrap(True)
        desc.setOpenExternalLinks(True)
        desc.setStyleSheet("color:#a9b4cc;font-size:12px;background:transparent;border:none;line-height:1.5;")
        lay.addWidget(desc)

        # Links grid
        links = [
            ("GitHub", "https://github.com/Borussia80/retromanager"),
            ("Bugs e sugestões", "https://github.com/Borussia80/retromanager/issues"),
        ]
        for label, url in links:
            row = QHBoxLayout()
            lbl_key = QLabel(f"{label}:")
            lbl_key.setStyleSheet("color:#6b7a99;font-size:11px;background:transparent;border:none;")
            lbl_key.setFixedWidth(110)
            lbl_val = QLabel(f"<a href='{url}' style='color:#4f8ef7;'>{url}</a>")
            lbl_val.setOpenExternalLinks(True)
            lbl_val.setStyleSheet("font-size:11px;background:transparent;border:none;")
            row.addWidget(lbl_key)
            row.addWidget(lbl_val, 1)
            lay.addLayout(row)

        # Divider
        div2 = QLabel()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background:#2e3a52;border:none;")
        lay.addWidget(div2)

        # Footer: license note + OK button
        footer = QHBoxLayout()
        lbl_license = QLabel("Distribuído sob a licença MIT.")
        lbl_license.setStyleSheet("color:#3d4f6e;font-size:10px;background:transparent;border:none;")
        footer.addWidget(lbl_license, 1)

        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(72)
        btn_ok.setStyleSheet("""
            QPushButton {
                background:#252d40;border:1px solid #2e3a52;border-radius:6px;
                padding:6px 16px;color:#a9b4cc;font-size:13px;
            }
            QPushButton:hover { background:#2e3a52;color:#e8ecf5; }
            QPushButton:pressed { background:#1a2030; }
        """)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        footer.addWidget(btn_ok)
        lay.addLayout(footer)
