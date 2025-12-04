import json
from typing import Any
from PySide6 import QtCore, QtGui, QtWidgets
from src.logic.spotdl_commands import get_user_playlists
from src.utils.config_manager import CONFIG
from src.utils.utils import PLAYLISTS_JSON_PATH


class AddView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.logic_thread = None
        self.worker = None

        add_layout = QtWidgets.QVBoxLayout(self)

        # Header
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setContentsMargins(0, 20, 0, 20)

        # Title label
        header_lbl = QtWidgets.QLabel(
            "<b>ADD PLAYLISTS</b>", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        font = QtGui.QFont()
        font.setPointSize(18)
        header_lbl.setFont(font)
        header_layout.addWidget(header_lbl)
        add_layout.addLayout(header_layout)

        # Top input fields
        input_layout = QtWidgets.QHBoxLayout()

        # Username label and input field
        username_lbl = QtWidgets.QLabel("Username")
        self.username_le = QtWidgets.QLineEdit()
        self.username_le.setText(CONFIG.get("username"))
        self.username_le.editingFinished.connect(
            lambda: self.search_playlists(self.username_le.text())
        )

        input_layout.addWidget(username_lbl)
        input_layout.addWidget(self.username_le)

        add_layout.addLayout(input_layout)

        # Playlist scroll list
        self.playlists_container_widget = None
        self.playlists_container_layout = None

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        add_layout.addWidget(self.scroll_area)

        # Footer
        footer_layout = QtWidgets.QVBoxLayout()
        footer_layout.setContentsMargins(0, 20, 0, 20)

        """
        sync_btn = QtWidgets.QPushButton("Sync All")
        sync_btn.clicked.connect(self.sync_all_playlists)

        horizontal_buttons_layout = QtWidgets.QHBoxLayout()
        enable_btn = QtWidgets.QPushButton("Enable All")
        enable_btn.clicked.connect(lambda: self.toggle_all_playlist(True))

        disable_btn = QtWidgets.QPushButton("Disable All")
        disable_btn.clicked.connect(lambda: self.toggle_all_playlist(False))

        horizontal_buttons_layout.addWidget(enable_btn)
        horizontal_buttons_layout.addWidget(disable_btn)

        footer_layout.addWidget(sync_btn)
        footer_layout.addLayout(horizontal_buttons_layout)
        """

        add_layout.addLayout(footer_layout)

        self.search_playlists("default")

    # TODO: THE SYNC OPERATIONS ARE BLOCKING ONES

    @QtCore.Slot(str)
    def search_playlists(self, username: str):
        if self.logic_thread and self.logic_thread.isRunning():
            print("Previous search is still running, cancelling...")
            return

        self.logic_thread = QtCore.QThread()
        self.worker = SearchPlaylistsWorker(username)
        self.worker.moveToThread(self.logic_thread)

        self.logic_thread.started.connect(self.worker.run)
        self.worker.updated_username.connect(self.update_username)
        self.worker.found_playlist.connect(self.show_playlist)

        self.worker.finished.connect(self.logic_thread.quit)

        self.logic_thread.finished.connect(self.worker.deleteLater)
        self.logic_thread.finished.connect(self.logic_thread.deleteLater)

        self.logic_thread.finished.connect(self.cleanup_thread)

        self.create_playlist_layout()
        self.logic_thread.start()

    @QtCore.Slot(dict)
    def show_playlist(self, playlist: dict[str, Any]):
        title = playlist.get("title", "N/A")
        url = playlist.get("url", "#")

        playlist_container = QtWidgets.QFrame()
        playlist_container.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        playlist_layout = QtWidgets.QVBoxLayout(playlist_container)

        # Title Label
        title_label = QtWidgets.QLabel(f"Title: <b>{title}</b>")
        title_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        playlist_layout.addWidget(title_label)

        # Url Label
        url_label = QtWidgets.QLabel(f"URL: <b>{url}</b>")
        url_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        playlist_layout.addWidget(url_label)

        # Playlist buttons layout
        buttons_layout = QtWidgets.QHBoxLayout()

        # Enabled Checkbox
        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_playlist)

        buttons_layout.addWidget(add_button, stretch=4)

        # Sync playlist button
        """
        sync_btn = QtWidgets.QPushButton("Sync Playlist")
        sync_btn.clicked.connect(
            lambda _, p_data=playlist: self.sync_playlist(p_data)
        )
        buttons_layout.addWidget(sync_btn, stretch=1)

        playlist_layout.addLayout(buttons_layout)
        """

        self.playlists_container_layout.addWidget(playlist_container)

    @QtCore.Slot()
    def update_username(self, new_username: str):
        self.username_le.setText(new_username)

    @QtCore.Slot()
    def add_playlist(self):
        print("ADDING")

    def cleanup_thread(self):
        self.worker = None
        self.logic_thread = None

    def create_playlist_layout(self):
        if self.playlists_container_widget is QtWidgets.QWidget:
            self.playlists_container_widget.deleteLater()

        self.playlists_container_widget = QtWidgets.QWidget()
        self.playlists_container_layout = QtWidgets.QVBoxLayout(
            self.playlists_container_widget
        )

        self.scroll_area.setWidget(self.playlists_container_widget)


class SearchPlaylistsWorker(QtCore.QObject):
    updated_username = QtCore.Signal(str)
    found_playlist = QtCore.Signal(dict)
    progress = QtCore.Signal(int)
    finished = QtCore.Signal()

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._is_cancelled = False

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

    def run(self):
        with open(PLAYLISTS_JSON_PATH, "r+") as file:
            try:
                self.data = json.load(file)
            except json.JSONDecodeError:
                self.data = {}
                json.dump(self.data, file, indent=2)
            except FileNotFoundError:
                print(f"Error: {PLAYLISTS_JSON_PATH} not found.")
                self.finished.emit()
                return

            if not self.username:
                self.finished.emit()
                return
            elif self.username == "default":
                if not self.data["username"]:
                    # Write a default value
                    self.data["username"] = "Spotify"
                    file.seek(0)
                    json.dump(self.data, file, indent=2)
                    self.updated_username.emit(self.username)
                else:
                    self.username = self.data["username"]
            else:
                # Write new value
                self.data["username"] = self.username
                file.seek(0)
                json.dump(self.data, file, indent=2)

            if not self.username:
                print("Could not find playlists: no username provided")
                self.finished.emit()
                return

        get_user_playlists(self.username, self.found_playlist)

        self.finished.emit()
