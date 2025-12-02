import json
from PySide6 import QtCore, QtWidgets
from src.utils.config_manager import CONFIG


class ManageView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.data = []
        self.checkboxes = []

        manage_layout = QtWidgets.QVBoxLayout(self)
        header_lbl = QtWidgets.QLabel(
            "<b>MANAGE PLAYLISTS</b>", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        manage_layout.addWidget(header_lbl)

    def parse_playlists(self):
        global PLAYLISTS_JSON_PATH

        self.checkboxes.clear()

        playlists = CONFIG.get("playlists")

        if not playlists:
            print("No added playlists found")
            return

        for i, playlist in enumerate(playlists):
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
    def toggle_playlist(self, checked, i):
        playlist = self.data[i]
        playlist["enabled"] = checked

        try:
            with open(PLAYLISTS_JSON_PATH, "w") as file:
                json.dump(self.data, file, indent=2)
        except IOError:
            print("Error writing to playlists JSON file.")
            return

    @QtCore.Slot(bool)
    def toggle_all_playlist(self, enabled):
        for playlist in self.data:
            playlist["enabled"] = enabled

        try:
            with open(PLAYLISTS_JSON_PATH, "w") as file:
                json.dump(self.data, file, indent=2)
        except IOError:
            print("Error writing to playlists JSON file.")
            return

    @QtCore.Slot(int)
    def sync_playlist(self, playlist):
        # TODO: Animation download this playlist
        syncPlaylist(playlist)

    @QtCore.Slot()
    def sync_all_playlists(self):
        for playlist in self.data:
            if playlist["enabled"]:
                # TODO: Animation download this playlist
                syncPlaylist(playlist)
