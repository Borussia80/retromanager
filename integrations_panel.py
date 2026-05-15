from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel


class _StatusRow(QWidget):
    """One integration row: dot + name + status text."""

    _STYLE_DOT_OFF  = "font-size:8px;color:#3d4f6e;background:transparent;border:none;"
    _STYLE_DOT_ON   = "font-size:8px;color:#34c97e;background:transparent;border:none;"
    _STYLE_NAME_OFF = "font-size:11px;font-weight:500;color:#6b7a99;background:transparent;border:none;"
    _STYLE_NAME_ON  = "font-size:11px;font-weight:500;color:#a9b4cc;background:transparent;border:none;"
    _STYLE_STAT_OFF = "font-size:10px;color:#3d4f6e;background:transparent;border:none;"
    _STYLE_STAT_ON  = "font-size:10px;color:#34c97e;background:transparent;border:none;"

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 2, 12, 2)
        lay.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(self._STYLE_DOT_OFF)

        self._lbl_name = QLabel(name)
        self._lbl_name.setStyleSheet(self._STYLE_NAME_OFF)

        self._lbl_status = QLabel("Não encontrado")
        self._lbl_status.setStyleSheet(self._STYLE_STAT_OFF)

        lay.addWidget(self._dot)
        lay.addWidget(self._lbl_name)
        lay.addStretch()
        lay.addWidget(self._lbl_status)

    def set_detected(self, status: str = "Detectado"):
        self._dot.setStyleSheet(self._STYLE_DOT_ON)
        self._lbl_name.setStyleSheet(self._STYLE_NAME_ON)
        self._lbl_status.setText(status)
        self._lbl_status.setStyleSheet(self._STYLE_STAT_ON)

    def set_missing(self):
        self._dot.setStyleSheet(self._STYLE_DOT_OFF)
        self._lbl_name.setStyleSheet(self._STYLE_NAME_OFF)
        self._lbl_status.setText("Não encontrado")
        self._lbl_status.setStyleSheet(self._STYLE_STAT_OFF)


