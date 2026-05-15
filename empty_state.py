from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class EmptyState(QWidget):
    """Reusable centred empty-state widget with icon, title, description and optional action."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(12)
        lay.setContentsMargins(40, 60, 40, 60)

        self._lbl_icon = QLabel()
        self._lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_icon.setStyleSheet(
            "font-size:38px;color:#2e3a52;background:transparent;border:none;"
        )
        lay.addWidget(self._lbl_icon)

        self._lbl_title = QLabel()
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_title.setStyleSheet(
            "font-size:15px;font-weight:600;color:#6b7a99;"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._lbl_title)

        self._lbl_desc = QLabel()
        self._lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_desc.setWordWrap(True)
        self._lbl_desc.setMaximumWidth(440)
        self._lbl_desc.setStyleSheet(
            "font-size:12px;color:#3d4f6e;background:transparent;border:none;"
        )
        lay.addWidget(self._lbl_desc)

        self._btn = QPushButton()
        self._btn.setVisible(False)
        self._btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn.setFixedWidth(210)
        self._btn.setStyleSheet("""
            QPushButton {
                background:#252d40;border:1px solid #2e3a52;border-radius:6px;
                padding:7px 20px;color:#a9b4cc;font-size:12px;
            }
            QPushButton:hover { background:#2e3a52;color:#e8ecf5; }
            QPushButton:pressed { background:#1a2030; }
        """)
        lay.addWidget(self._btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_content(self, icon: str, title: str, description: str,
                    action_label: str = None, action_callback=None):
        self._lbl_icon.setText(icon)
        self._lbl_icon.setVisible(bool(icon))
        self._lbl_title.setText(title)
        self._lbl_desc.setText(description)

        try:
            self._btn.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass

        if action_label and action_callback:
            self._btn.setText(action_label)
            self._btn.clicked.connect(action_callback)
            self._btn.setVisible(True)
        else:
            self._btn.setVisible(False)
