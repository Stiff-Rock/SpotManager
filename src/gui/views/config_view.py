import os
from PySide6 import QtCore, QtGui, QtWidgets
from src.utils.config_manager import CONFIG


class ConfigView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        outer_layout = QtWidgets.QVBoxLayout(self)

        outer_layout.addStretch()

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)

        # Header
        header_lbl = QtWidgets.QLabel(
            "<b>CONFIGURATION</b>", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        font = QtGui.QFont()
        font.setPointSize(18)
        header_lbl.setFont(font)
        content_layout.addWidget(header_lbl)

        path_row = QtWidgets.QHBoxLayout()
        self.path_le = QtWidgets.QLineEdit(CONFIG.get_playlists_path())
        self.path_le.textChanged.connect(self._validate_path)
        self.path_le.setPlaceholderText("Select download folder...")
        path_row.addWidget(self.path_le)

        select_folder_btn = QtWidgets.QPushButton("📁")
        select_folder_btn.clicked.connect(self._select_path)
        path_row.addWidget(select_folder_btn)
        content_layout.addLayout(path_row)

        self.error_container = QtWidgets.QWidget()
        self.error_container.setFixedHeight(30)
        error_layout = QtWidgets.QVBoxLayout(self.error_container)
        error_layout.setContentsMargins(0, 0, 0, 0)

        self.error_lbl = QtWidgets.QLabel("Invalid path")
        self.error_lbl.setStyleSheet("color: #d65d5d;")
        self.error_lbl.hide()
        error_layout.addWidget(self.error_lbl)

        content_layout.addWidget(self.error_container)

        outer_layout.addWidget(content_widget)

        outer_layout.addStretch()

    def _validate_path(self, path: str):
        if not os.path.isdir(path):
            self.error_lbl.show()
        else:
            self.error_lbl.hide()
            self._save_path(path)

    def _select_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Folder", os.path.expanduser("~")
        )
        if folder:
            self._save_path(folder)

    def _save_path(self, path: str):
        self.path_le.setText(path)
        CONFIG.set_playlists_path(path)
