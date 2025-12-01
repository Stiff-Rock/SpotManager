import json
from PySide6 import QtCore, QtGui, QtWidgets

from spotdl_commands import syncPlaylist

PLAYLISTS_JSON_PATH = "playlists.json"


class SpotWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.resize(850, 600)
        self.setWindowTitle("SpotManager")

        self.p_data = []
        self.checkboxes = []

        window_layout = QtWidgets.QVBoxLayout(self)

        # Header
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setContentsMargins(0, 20, 0, 20)
        header_lbl = QtWidgets.QLabel(
            "<b>MANAGE PLAYLISTS</b>", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        font = QtGui.QFont()
        font.setPointSize(18)
        header_lbl.setFont(font)

        header_layout.addWidget(header_lbl)
        window_layout.addLayout(header_layout)

        # Playlist list
        playlists_container_widget = QtWidgets.QWidget()
        self.playlists_container_layout = QtWidgets.QVBoxLayout(
            playlists_container_widget
        )

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(playlists_container_widget)

        window_layout.addWidget(scroll_area)

        # Footer
        footer_layout = QtWidgets.QVBoxLayout()
        footer_layout.setContentsMargins(0, 20, 0, 20)

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

        window_layout.addLayout(footer_layout)

        self.parse_playlists()

    # TODO: THE SYNC OPERATIONS ARE BLOCKING ONES

    def parse_playlists(self):
        global PLAYLISTS_JSON_PATH

        self.checkboxes.clear()

        with open(PLAYLISTS_JSON_PATH, "r") as file:
            try:
                self.p_data = json.load(file)
            except FileNotFoundError:
                print(f"Error: {PLAYLISTS_JSON_PATH} not found.")
                return

            for i, playlist in enumerate(self.p_data):
                title = playlist.get("title", "N/A")
                url = playlist.get("url", "#")
                enabled = playlist.get("enabled", False)

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
                enabled_checkbox = QtWidgets.QCheckBox("Enabled: ")
                enabled_checkbox.setChecked(enabled)
                enabled_checkbox.toggled.connect(
                    lambda checked, i=i: self.manual_toggle_playlist(checked, i)
                )
                self.checkboxes.append(enabled_checkbox)
                buttons_layout.addWidget(enabled_checkbox, stretch=4)

                # Sync playlist button
                sync_btn = QtWidgets.QPushButton("Sync Playlist")
                sync_btn.clicked.connect(
                    lambda _, p_data=playlist: self.sync_playlist(p_data)
                )
                buttons_layout.addWidget(sync_btn, stretch=1)

                playlist_layout.addLayout(buttons_layout)

                self.playlists_container_layout.addWidget(playlist_container)

    @QtCore.Slot(bool, int)
    def manual_toggle_playlist(self, checked, i):
        playlist = self.p_data[i]
        playlist["enabled"] = checked

        try:
            with open(PLAYLISTS_JSON_PATH, "w") as file:
                json.dump(self.p_data, file, indent=2)
        except IOError:
            print("Error writing to playlists JSON file.")
            return

    @QtCore.Slot(bool)
    def toggle_all_playlist(self, enabled):
        for i, playlist in enumerate(self.p_data):
            playlist["enabled"] = enabled
            checkbox = self.checkboxes[i]
            checkbox.blockSignals(True)
            checkbox.setChecked(enabled)
            checkbox.blockSignals(False)

        try:
            with open(PLAYLISTS_JSON_PATH, "w") as file:
                json.dump(self.p_data, file, indent=2)
        except IOError:
            print("Error writing to playlists JSON file.")
            return

    @QtCore.Slot(int)
    def sync_playlist(self, playlist):
        # TODO: Animation download this playlist
        syncPlaylist(playlist)

    @QtCore.Slot()
    def sync_all_playlists(self):
        for playlist in self.p_data:
            if playlist["enabled"]:
                # TODO: Animation download this playlist
                syncPlaylist(playlist)
