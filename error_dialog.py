import os
from itertools import zip_longest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)


class DownloadErrorDialog(QDialog):
    def __init__(self, rom_name: str, platform: str, reason: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Falha no download")
        self.setModal(True)
        self.setFixedWidth(440)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet("""
            QDialog {
                background: #1a1f2e;
                border: 1px solid #3d4f6e;
                border-radius: 10px;
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

        lbl_title = QLabel("Falha no download")
        lbl_title.setStyleSheet("font-size:16px;font-weight:600;color:#e8ecf5;")

        hdr.addWidget(icon)
        hdr.addWidget(lbl_title, 1)
        lay.addLayout(hdr)

        # ROM name block — uniform monospaced font, no mixed weights
        lbl_rom = QLabel(f"[{platform}]  {rom_name}")
        lbl_rom.setStyleSheet(
            "background:#252d40;border-radius:6px;padding:10px 14px;"
            "font-size:13px;color:#a9b4cc;font-family:monospace;"
        )
        lbl_rom.setWordWrap(True)
        lay.addWidget(lbl_rom)

        # Error reason
        lbl_reason = QLabel(reason)
        lbl_reason.setStyleSheet("font-size:12px;color:#f04a5a;")
        lbl_reason.setWordWrap(True)
        lay.addWidget(lbl_reason)

        # Hint — Portuguese
        lbl_hint = QLabel("O item permanece na fila — você pode tentar novamente.")
        lbl_hint.setStyleSheet("font-size:11px;color:#6b7a99;")
        lbl_hint.setWordWrap(True)
        lay.addWidget(lbl_hint)

        lay.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_retry = QPushButton("↺  Tentar novamente")
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


def _char_diff_html(actual: str, expected: str) -> tuple[str, str]:
    """Return (actual_html, expected_html) with mismatching chars highlighted."""
    act_parts: list[str] = []
    exp_parts: list[str] = []
    for a, e in zip_longest(actual, expected, fillvalue=""):
        if a.lower() == e.lower():
            act_parts.append(a)
            exp_parts.append(e)
        else:
            if a:
                act_parts.append(
                    f'<span style="background:#3d1a1e;color:#f04a5a;">{a}</span>'
                )
            if e:
                exp_parts.append(
                    f'<span style="background:#1a3a26;color:#34c97e;">{e}</span>'
                )
    return "".join(act_parts), "".join(exp_parts)


_COPY_BTN_STYLE = """
    QPushButton {
        background:#252d40;border:1px solid #2e3a52;border-radius:4px;
        padding:2px 8px;color:#6b7a99;font-size:10px;
    }
    QPushButton:hover { background:#2e3a52;color:#e8ecf5; }
    QPushButton:pressed { background:#1a2030; }
"""


class HashResultDialog(QDialog):
    def __init__(self, file_path: str, results: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verificação de integridade")
        self.setModal(True)
        self.setFixedWidth(520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog { background:#1a1f2e; border:1px solid #3d4f6e; border-radius:10px; }
            QLabel  { background:transparent; border:none; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(12)

        # Determine overall pass/fail
        all_ok = all(
            (not exp or act.lower() == exp.lower())
            for act, exp in results.values()
        )
        failed_count = sum(
            1 for act, exp in results.values()
            if exp and act.lower() != exp.lower()
        )
        checked_count = sum(1 for _, exp in results.values() if exp)

        # Header
        hdr = QHBoxLayout()
        icon_ch = "✓" if all_ok else "✕"
        icon_bg = "#1a3a26" if all_ok else "#3d1a1e"
        icon_fg = "#34c97e" if all_ok else "#f04a5a"
        icon_lbl = QLabel(icon_ch)
        icon_lbl.setFixedSize(38, 38)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background:{icon_bg};color:{icon_fg};"
            "border-radius:19px;font-size:15px;font-weight:bold;"
        )
        if all_ok:
            title_txt = "Integridade verificada"
        else:
            title_txt = (
                f"Falha na verificação  ·  "
                f"{failed_count} de {checked_count} algoritmos divergem"
            )
        lbl_title = QLabel(title_txt)
        lbl_title.setStyleSheet("font-size:15px;font-weight:600;color:#e8ecf5;")
        hdr.addWidget(icon_lbl)
        hdr.addWidget(lbl_title, 1)
        lay.addLayout(hdr)

        # File path
        lbl_file = QLabel(os.path.basename(file_path))
        lbl_file.setStyleSheet(
            "background:#252d40;border-radius:6px;padding:8px 14px;"
            "font-size:12px;color:#a9b4cc;font-family:monospace;"
        )
        lbl_file.setToolTip(file_path)
        lay.addWidget(lbl_file)

        # Hash rows
        for name, (actual, expected) in results.items():
            ok = not expected or actual.lower() == expected.lower()

            row = QHBoxLayout()
            row.setSpacing(8)

            lbl_name = QLabel(name)
            lbl_name.setFixedWidth(48)
            lbl_name.setStyleSheet("font-size:11px;font-weight:600;color:#6b7a99;")

            if ok or not expected:
                lbl_val = QLabel(actual)
                lbl_val.setStyleSheet(
                    "font-size:11px;color:#a9b4cc;font-family:monospace;"
                )
            else:
                act_html, _ = _char_diff_html(actual, expected)
                lbl_val = QLabel(act_html)
                lbl_val.setTextFormat(Qt.TextFormat.RichText)
                lbl_val.setStyleSheet("font-size:11px;font-family:monospace;")

            lbl_status = QLabel("✓" if ok else "✗")
            lbl_status.setFixedWidth(18)
            lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_status.setStyleSheet(
                f"font-size:13px;font-weight:bold;color:{'#34c97e' if ok else '#f04a5a'};"
            )

            btn_copy = QPushButton("⎘")
            btn_copy.setFixedSize(26, 20)
            btn_copy.setToolTip(f"Copiar {name}")
            btn_copy.setStyleSheet(_COPY_BTN_STYLE)
            _val = actual
            btn_copy.clicked.connect(
                lambda _, v=_val: QApplication.clipboard().setText(v)
            )

            row.addWidget(lbl_name)
            row.addWidget(lbl_val, 1)
            row.addWidget(lbl_status)
            row.addWidget(btn_copy)
            lay.addLayout(row)

            if not ok and expected:
                _, exp_html = _char_diff_html(actual, expected)
                exp_row = QHBoxLayout()
                exp_row.setSpacing(8)
                exp_row.addSpacing(56)
                lbl_exp_tag = QLabel("esp.")
                lbl_exp_tag.setFixedWidth(32)
                lbl_exp_tag.setStyleSheet("font-size:10px;color:#3d4f6e;")
                lbl_exp = QLabel(exp_html)
                lbl_exp.setTextFormat(Qt.TextFormat.RichText)
                lbl_exp.setStyleSheet("font-size:11px;font-family:monospace;color:#34c97e;")
                exp_row.addWidget(lbl_exp_tag)
                exp_row.addWidget(lbl_exp, 1)
                lay.addLayout(exp_row)

        lay.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        if all_ok:
            btn_ok = QPushButton("OK")
            btn_ok.setFixedWidth(72)
            btn_ok.setStyleSheet("""
                QPushButton {
                    background:#252d40;border:1px solid #2e3a52;border-radius:6px;
                    padding:8px 20px;color:#a9b4cc;font-size:13px;
                }
                QPushButton:hover  { background:#2e3a52;color:#e8ecf5; }
                QPushButton:pressed{ background:#1a2030; }
            """)
            btn_ok.clicked.connect(self.reject)
            btn_ok.setDefault(True)
            btn_row.addWidget(btn_ok)
        else:
            btn_keep = QPushButton("Manter arquivo")
            btn_keep.setStyleSheet("""
                QPushButton {
                    background:#252d40;border:1px solid #2e3a52;border-radius:6px;
                    padding:8px 16px;color:#a9b4cc;font-size:13px;
                }
                QPushButton:hover  { background:#2e3a52;color:#e8ecf5; }
                QPushButton:pressed{ background:#1a2030; }
            """)
            btn_keep.clicked.connect(self.reject)

            btn_redownload = QPushButton("↺  Re-baixar")
            btn_redownload.setStyleSheet("""
                QPushButton {
                    background:#4f8ef7;border:none;border-radius:6px;
                    padding:8px 16px;color:#fff;font-weight:600;font-size:13px;
                }
                QPushButton:hover  { background:#3a6fd4; }
                QPushButton:pressed{ background:#2e5ab0; }
            """)
            btn_redownload.clicked.connect(self.accept)
            btn_redownload.setDefault(True)

            btn_row.addWidget(btn_keep)
            btn_row.addWidget(btn_redownload)

        lay.addLayout(btn_row)
