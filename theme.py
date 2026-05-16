DARK_THEME = """
QWidget {
    background-color: #0f1117;
    color: #e8ecf5;
    font-family: "Inter", "Segoe UI", "Liberation Sans", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #0f1117;
}
QListWidget, QTableWidget {
    background-color: #161b27;
    border: 1px solid #2e3a52;
    border-radius: 6px;
    outline: none;
}
QListWidget::item {
    padding: 2px 0;
    border: none;
}
QListWidget::item:selected {
    background-color: #1e2d4a;
    color: #e8ecf5;
    border-radius: 4px;
}
QListWidget::item:hover:!selected {
    background-color: #1e2535;
    border-radius: 4px;
}
QTableWidget::item:selected {
    background-color: #1e2d4a;
    color: #e8ecf5;
}
QTableWidget::item:hover:!selected {
    background-color: #1e2535;
}
QLineEdit {
    background-color: #1e2535;
    border: 1px solid #2e3a52;
    border-radius: 6px;
    padding: 5px 10px;
    color: #e8ecf5;
    selection-background-color: #4f8ef7;
}
QLineEdit:focus {
    border-color: #4f8ef7;
}
QPushButton {
    background-color: #1e2535;
    border: 1px solid #2e3a52;
    border-radius: 5px;
    padding: 4px 12px;
    color: #a9b4cc;
}
QPushButton:hover {
    background-color: #252d40;
    color: #e8ecf5;
}
QPushButton:pressed {
    background-color: #1a2030;
}
QPushButton:checked {
    background-color: #4f8ef7;
    border-color: #4f8ef7;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: #161b27;
    color: #3d4f6e;
    border-color: #1e2535;
}
QHeaderView::section {
    background-color: #1e2535;
    border: none;
    border-bottom: 1px solid #2e3a52;
    border-right: 1px solid #2e3a52;
    padding: 5px 8px;
    font-size: 10px;
    font-weight: 600;
    color: #6b7a99;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
QHeaderView::section:last {
    border-right: none;
}
QScrollBar:vertical {
    background: #161b27;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2e3a52;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3d4f6e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #161b27;
    height: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2e3a52;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QSplitter::handle {
    background: #2e3a52;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QStatusBar {
    background: #161b27;
    border-top: 1px solid #2e3a52;
    font-size: 11px;
    color: #6b7a99;
}
QStatusBar QLabel {
    color: #6b7a99;
    font-size: 11px;
    padding: 0 6px;
}
QMenuBar {
    background-color: #161b27;
    border-bottom: 1px solid #2e3a52;
    color: #a9b4cc;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #1e2535;
    border-radius: 4px;
    color: #e8ecf5;
}
QMenu {
    background-color: #1e2535;
    border: 1px solid #2e3a52;
    border-radius: 6px;
    padding: 4px;
    color: #e8ecf5;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #252d40;
}
QMenu::separator {
    height: 1px;
    background: #2e3a52;
    margin: 4px 8px;
}
QToolTip {
    background-color: #1e2535;
    color: #e8ecf5;
    border: 1px solid #2e3a52;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QMessageBox {
    background-color: #161b27;
}
QProgressBar {
    background-color: #252d40;
    border-radius: 3px;
    border: none;
}
QProgressBar::chunk {
    background-color: #4f8ef7;
    border-radius: 3px;
}
QGroupBox {
    border: 1px solid #2e3a52;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    color: #6b7a99;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QComboBox {
    background-color: #1e2535;
    border: 1px solid #2e3a52;
    border-radius: 5px;
    padding: 4px 8px;
    color: #e8ecf5;
}
QComboBox:focus {
    border-color: #4f8ef7;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1e2535;
    border: 1px solid #2e3a52;
    selection-background-color: #252d40;
    color: #e8ecf5;
}
QCheckBox {
    color: #a9b4cc;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #2e3a52;
    background: #1e2535;
}
QCheckBox::indicator:checked {
    background: #4f8ef7;
    border-color: #4f8ef7;
}
QAbstractScrollArea {
    background-color: #161b27;
}
"""

LIGHT_THEME = """
QWidget {
    background-color: #f5f7fa;
    color: #1a2035;
    font-family: "Inter", "Segoe UI", "Liberation Sans", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #f5f7fa;
}
QListWidget, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7e6;
    border-radius: 6px;
    outline: none;
}
QListWidget::item {
    padding: 2px 0;
    border: none;
}
QListWidget::item:selected {
    background-color: #d6e4ff;
    color: #1a2035;
    border-radius: 4px;
}
QListWidget::item:hover:!selected {
    background-color: #eef2fb;
    border-radius: 4px;
}
QTableWidget::item:selected {
    background-color: #d6e4ff;
    color: #1a2035;
}
QTableWidget::item:hover:!selected {
    background-color: #eef2fb;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c4cfe0;
    border-radius: 6px;
    padding: 5px 10px;
    color: #1a2035;
    selection-background-color: #3b7de9;
}
QLineEdit:focus {
    border-color: #3b7de9;
}
QPushButton {
    background-color: #eef0f6;
    border: 1px solid #c4cfe0;
    border-radius: 5px;
    padding: 4px 12px;
    color: #3a4a6b;
}
QPushButton:hover {
    background-color: #e0e6f5;
    color: #1a2035;
}
QPushButton:pressed {
    background-color: #d0d9ef;
}
QPushButton:checked {
    background-color: #3b7de9;
    border-color: #3b7de9;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: #f0f2f8;
    color: #b0bdd0;
    border-color: #dce3ef;
}
QHeaderView::section {
    background-color: #eef0f6;
    border: none;
    border-bottom: 1px solid #d0d7e6;
    border-right: 1px solid #d0d7e6;
    padding: 5px 8px;
    font-size: 10px;
    font-weight: 600;
    color: #5a6a8c;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
QHeaderView::section:last {
    border-right: none;
}
QScrollBar:vertical {
    background: #f0f2f8;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c4cfe0;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #a0b0cc;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #f0f2f8;
    height: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #c4cfe0;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QSplitter::handle {
    background: #d0d7e6;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QStatusBar {
    background: #eef0f6;
    border-top: 1px solid #d0d7e6;
    font-size: 11px;
    color: #5a6a8c;
}
QStatusBar QLabel {
    color: #5a6a8c;
    font-size: 11px;
    padding: 0 6px;
}
QMenuBar {
    background-color: #eef0f6;
    border-bottom: 1px solid #d0d7e6;
    color: #3a4a6b;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #e0e6f5;
    border-radius: 4px;
    color: #1a2035;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d7e6;
    border-radius: 6px;
    padding: 4px;
    color: #1a2035;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #eef2fb;
}
QMenu::separator {
    height: 1px;
    background: #d0d7e6;
    margin: 4px 8px;
}
QToolTip {
    background-color: #ffffff;
    color: #1a2035;
    border: 1px solid #d0d7e6;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QMessageBox {
    background-color: #f5f7fa;
}
QProgressBar {
    background-color: #e0e6f5;
    border-radius: 3px;
    border: none;
}
QProgressBar::chunk {
    background-color: #3b7de9;
    border-radius: 3px;
}
QGroupBox {
    border: 1px solid #d0d7e6;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    color: #5a6a8c;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #c4cfe0;
    border-radius: 5px;
    padding: 4px 8px;
    color: #1a2035;
}
QComboBox:focus {
    border-color: #3b7de9;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d7e6;
    selection-background-color: #eef2fb;
    color: #1a2035;
}
QCheckBox {
    color: #3a4a6b;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #c4cfe0;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #3b7de9;
    border-color: #3b7de9;
}
QAbstractScrollArea {
    background-color: #ffffff;
}
"""


def apply_theme(app, theme: str) -> None:
    """Apply dark, light, or system theme to the QApplication."""
    from PyQt6.QtGui import QPalette

    resolved = theme
    if theme == "system":
        palette = app.palette()
        lightness = palette.color(QPalette.ColorRole.Window).lightness()
        resolved = "dark" if lightness < 128 else "light"

    app.setStyleSheet(DARK_THEME if resolved == "dark" else LIGHT_THEME)
