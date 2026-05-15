# ─────────────────────────────────────────────────────────────────────────────
# AVISO: arquivo originalmente gerado por pyuic6 a partir de um .ui que não
# está mais acessível. Agora é editado À MÃO e é source-of-truth da janela
# de Opções.
# NÃO REGENERAR com pyuic6 — perderia todas as customizações
# (i18n pt-BR, presets de cache, tab Integrações, etc.).
# ─────────────────────────────────────────────────────────────────────────────


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        Dialog.resize(560, 300)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/app.ico"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        Dialog.setWindowIcon(icon)

        # ── Root layout ───────────────────────────────────────────────────────
        root = QtWidgets.QVBoxLayout(Dialog)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Tab widget ────────────────────────────────────────────────────────
        self.tab_widget = QtWidgets.QTabWidget(Dialog)
        self.tab_widget.setObjectName("tab_widget")

        # ── Tab 1: Geral ──────────────────────────────────────────────────────
        self.tab_geral = QtWidgets.QWidget()
        self.tab_geral.setObjectName("tab_geral")
        geral_lay = QtWidgets.QVBoxLayout(self.tab_geral)
        geral_lay.setContentsMargins(8, 12, 8, 8)
        geral_lay.setSpacing(8)

        # Cache e biblioteca
        self.gbCacheAndDatabase = QtWidgets.QGroupBox(parent=self.tab_geral)
        self.gbCacheAndDatabase.setObjectName("gbCacheAndDatabase")
        cache_lay = QtWidgets.QHBoxLayout(self.gbCacheAndDatabase)
        cache_lay.setObjectName("horizontalLayout")

        self.label = QtWidgets.QLabel(parent=self.gbCacheAndDatabase)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                  QtWidgets.QSizePolicy.Policy.Maximum)
        )
        self.label.setObjectName("label")
        cache_lay.addWidget(self.label)

        self.cb_cache_expiration = QtWidgets.QComboBox(parent=self.gbCacheAndDatabase)
        self.cb_cache_expiration.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                  QtWidgets.QSizePolicy.Policy.Maximum)
        )
        self.cb_cache_expiration.setObjectName("cb_cache_expiration")
        # Items are populated dynamically in options.py via addItem(label, userData)
        cache_lay.addWidget(self.cb_cache_expiration)
        geral_lay.addWidget(self.gbCacheAndDatabase)

        # Pasta de download
        self.groupBox_3 = QtWidgets.QGroupBox(parent=self.tab_geral)
        self.groupBox_3.setObjectName("groupBox_3")
        path_lay = QtWidgets.QHBoxLayout(self.groupBox_3)
        path_lay.setObjectName("horizontalLayout_2")

        self.label_3 = QtWidgets.QLabel(parent=self.groupBox_3)
        self.label_3.setObjectName("label_3")
        path_lay.addWidget(self.label_3)

        self.le_DownloadPath = QtWidgets.QLineEdit(parent=self.groupBox_3)
        self.le_DownloadPath.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding,
                                  QtWidgets.QSizePolicy.Policy.Minimum)
        )
        self.le_DownloadPath.setObjectName("le_DownloadPath")
        path_lay.addWidget(self.le_DownloadPath)

        self.pb_BrowsePath = QtWidgets.QPushButton(parent=self.groupBox_3)
        self.pb_BrowsePath.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed,
                                  QtWidgets.QSizePolicy.Policy.Minimum)
        )
        self.pb_BrowsePath.setObjectName("pb_BrowsePath")
        path_lay.addWidget(self.pb_BrowsePath)
        geral_lay.addWidget(self.groupBox_3)

        # Comportamento
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.tab_geral)
        self.groupBox_2.setObjectName("groupBox_2")
        misc_lay = QtWidgets.QHBoxLayout(self.groupBox_2)
        misc_lay.setObjectName("horizontalLayout_3")

        self.cb_unzip = QtWidgets.QCheckBox(parent=self.groupBox_2)
        self.cb_unzip.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                  QtWidgets.QSizePolicy.Policy.Maximum)
        )
        self.cb_unzip.setObjectName("cb_unzip")
        misc_lay.addWidget(self.cb_unzip)

        self.cb_checkupdates = QtWidgets.QCheckBox(parent=self.groupBox_2)
        self.cb_checkupdates.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                  QtWidgets.QSizePolicy.Policy.Maximum)
        )
        self.cb_checkupdates.setObjectName("cb_checkupdates")
        misc_lay.addWidget(self.cb_checkupdates)
        geral_lay.addWidget(self.groupBox_2)

        geral_lay.addStretch()
        self.tab_widget.addTab(self.tab_geral, "Geral")

        # ── Tab 2: Integrações ────────────────────────────────────────────────
        # Content is built programmatically in options.py after helpers are known
        self.tab_integrations = QtWidgets.QWidget()
        self.tab_integrations.setObjectName("tab_integrations")
        self.tab_widget.addTab(self.tab_integrations, "Integrações")

        root.addWidget(self.tab_widget)

        # ── Button box ────────────────────────────────────────────────────────
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog)
        self.buttonBox.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                  QtWidgets.QSizePolicy.Policy.Preferred)
        )
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel |
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self.buttonBox.setObjectName("buttonBox")
        root.addWidget(self.buttonBox, 0, QtCore.Qt.AlignmentFlag.AlignBottom)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)  # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Configurações"))
        self.tab_widget.setTabText(0, _translate("Dialog", "Geral"))
        self.tab_widget.setTabText(1, _translate("Dialog", "Integrações"))
        self.gbCacheAndDatabase.setTitle(_translate("Dialog", "Cache e biblioteca"))
        self.label.setText(_translate("Dialog", "Atualizar catálogo a cada (dias)"))
        # cb_cache_expiration items são populados dinamicamente em options.py com userData
        self.groupBox_3.setTitle(_translate("Dialog", "Pasta de download"))
        self.label_3.setText(_translate("Dialog", "Pasta de download"))
        self.pb_BrowsePath.setText(_translate("Dialog", "Escolher…"))
        self.groupBox_2.setTitle(_translate("Dialog", "Comportamento"))
        self.cb_unzip.setText(_translate("Dialog", "Descompactar após baixar"))
        self.cb_checkupdates.setText(_translate("Dialog", "Buscar atualizações ao iniciar"))
