import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QWidget, QFileDialog,
)

from ui.ui_Options import Ui_Dialog as Ui
from _settings import SettingsHelper
from integrations_panel import _StatusRow
from theme import apply_theme


_CACHE_PRESETS = [
    ("A cada 30 dias (recomendado)", 30),
    ("A cada 7 dias",                 7),
    ("A cada 90 dias",               90),
    ("A cada inicialização",          1),
    ("Nunca (modo offline)",         -1),
]

_THEME_PRESETS = [
    ("Escuro (padrão)", "dark"),
    ("Claro",           "light"),
    ("Sistema",         "system"),
]


class Options(QDialog, Ui):
    _settings: SettingsHelper

    def __init__(self, parent, settings: SettingsHelper, retroarch=None, lutris=None):
        super().__init__(parent)
        self._settings = settings
        self._retroarch = retroarch
        self._lutris = lutris

        self.setupUi(self)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)

        for label, days in _CACHE_PRESETS:
            self.cb_cache_expiration.addItem(label, days)

        for label, value in _THEME_PRESETS:
            self.cb_theme.addItem(label, value)

        self.le_DownloadPath.setAcceptDrops(True)

        self._build_integrations_tab()

        self.pb_BrowsePath.clicked.connect(self._onBrowsePathClicked)
        self.accepted.connect(self._onAccept)

    # ── Tab Integrações ───────────────────────────────────────────────────────

    def _build_integrations_tab(self):
        lay = QVBoxLayout(self.tab_integrations)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(6)

        self._ra_status, ra_widget = self._make_row("RetroArch", self._retroarch)
        self._lt_status, lt_widget = self._make_row("Lutris",    self._lutris)

        lay.addWidget(ra_widget)
        lay.addWidget(lt_widget)
        lay.addStretch()

    def _make_row(self, name: str, helper) -> tuple:
        """Returns (_StatusRow, container QWidget) for one integration."""
        container = QWidget(self.tab_integrations)
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        status = _StatusRow(name)

        btn = QPushButton("Configurar…")
        btn.setFixedWidth(100)
        btn.setStyleSheet("""
            QPushButton {
                background:#252d40;border:1px solid #2e3a52;border-radius:5px;
                padding:4px 12px;color:#a9b4cc;font-size:12px;
            }
            QPushButton:hover { background:#2e3a52;color:#e8ecf5; }
        """)
        path = ''
        if helper and helper.detected:
            path = getattr(helper, 'config_dir', None) or getattr(helper, 'exe', None) or ''
            status.set_detected()

        btn.clicked.connect(lambda _checked, n=name, p=path: self._show_info(n, p))

        row.addWidget(status, 1)
        row.addWidget(btn)
        return status, container

    def _show_info(self, name: str, path: str):
        if path:
            QMessageBox.information(
                self, name,
                f"<b>{name}</b> detectado em:<br><code>{path}</code>",
            )
        else:
            QMessageBox.information(
                self, name,
                f"<b>{name}</b> não foi encontrado automaticamente.<br><br>"
                "Instale via repositório ou Flatpak e reinicie o Retromanager.",
            )

    def refresh_integrations(self):
        """Update row status after RetroArch/Lutris state changes."""
        if self._retroarch:
            if self._retroarch.detected:
                count = self._retroarch.total_playlist_items()
                txt = f"{count:,} na playlist".replace(",", ".") if count else "Ativo"
                self._ra_status.set_detected(txt)
            else:
                self._ra_status.set_missing()
        if self._lutris:
            if self._lutris.detected:
                count = self._lutris.game_count()
                txt = f"{count:,} jogos".replace(",", ".") if count else "Ativo"
                self._lt_status.set_detected(txt)
            else:
                self._lt_status.set_missing()

    # ── Tab Geral ─────────────────────────────────────────────────────────────

    def show(self) -> None:
        days = self._settings.get('cache_expiration')
        idx = self.cb_cache_expiration.findData(days)
        self.cb_cache_expiration.setCurrentIndex(idx if idx >= 0 else 0)

        self.le_DownloadPath.setText(self._settings.get('download_path'))
        self.cb_unzip.setChecked(self._settings.get('unzip'))
        self.cb_checkupdates.setChecked(self._settings.get('check_updates'))

        theme = self._settings.get('theme')
        t_idx = self.cb_theme.findData(theme)
        self.cb_theme.setCurrentIndex(t_idx if t_idx >= 0 else 0)

        return super().show()

    def _onBrowsePathClicked(self):
        new_path = QFileDialog.getExistingDirectory()
        if new_path:
            self.le_DownloadPath.setText(new_path)

    def _onAccept(self):
        days = self.cb_cache_expiration.currentData()
        if days is not None:
            self._settings.update(['cache_expiration', days])

        if os.path.isdir(self.le_DownloadPath.text()):
            self._settings.update(['download_path', self.le_DownloadPath.text()])

        self._settings.update(['unzip', self.cb_unzip.isChecked()])
        self._settings.update(['check_updates', self.cb_checkupdates.isChecked()])

        new_theme = self.cb_theme.currentData()
        if new_theme:
            self._settings.update(['theme', new_theme])
            apply_theme(QApplication.instance(), new_theme)

        self._settings.write()
