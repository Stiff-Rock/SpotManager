from typing import Literal
from PySide6 import QtCore, QtWidgets
from src.logic.spotdl_commands import syncPlaylist
from src.utils.config_manager import CONFIG, PlaylistData

CARD_MARGIN = 10
MAX_HEIGHT = 130

CardType = Literal["search", "manage"]


class PlaylistCard(QtWidgets.QWidget):
    on_add_playlist = QtCore.Signal(dict)
    on_delete = QtCore.Signal()

    def __init__(self, type: CardType, new_playlist: PlaylistData):
        super().__init__()

        self.setMaximumHeight(MAX_HEIGHT)

        self.playlist = new_playlist

        title = new_playlist.get("title", "N/A")
        total_tracks = new_playlist.get("total_tracks", "-1")
        url = self.playlist.get("url", "#")
        p_id = new_playlist.get("id")

        top_layout = QtWidgets.QVBoxLayout(self)
        top_layout.setContentsMargins(
            CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN
        )

        self.playlist_card = QtWidgets.QFrame()
        self.playlist_card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        top_layout.addWidget(self.playlist_card)

        playlist_layout = QtWidgets.QVBoxLayout(self.playlist_card)

        # Title Label
        title_label = QtWidgets.QLabel(f"Title: <b>{title}</b>")
        title_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        playlist_layout.addWidget(title_label)

        # Total Tracks Label
        total_tracks_label = QtWidgets.QLabel(f"Total Tracks: <b>{total_tracks}</b>")
        total_tracks_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        playlist_layout.addWidget(total_tracks_label)

        # Url Label
        url_label = QtWidgets.QLabel(f"URL: <b>{url}</b>")
        url_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        playlist_layout.addWidget(url_label)

        if type == "search":
            # Add playlist button
            add_btn = QtWidgets.QPushButton("Add")
            add_btn.clicked.connect(
                lambda _, p=self.playlist: self.on_add_playlist.emit(p)
            )
            playlist_layout.addWidget(add_btn)
        else:
            buttons_layout = QtWidgets.QHBoxLayout()

            self.enabled_checkbox = QtWidgets.QCheckBox("Enabled: ")
            self.enabled_checkbox.setChecked(True)
            self.enabled_checkbox.toggled.connect(self.toggle_playlist)
            buttons_layout.addWidget(self.enabled_checkbox, stretch=8)

            sync_btn = QtWidgets.QPushButton("Sync")
            sync_btn.clicked.connect(lambda _, p=new_playlist: self._sync_playlist(p))
            buttons_layout.addWidget(sync_btn, stretch=2)

            remove_btn = QtWidgets.QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, p_id=p_id: self._remove_playlist(p_id))
            buttons_layout.addWidget(remove_btn, stretch=2)

            playlist_layout.addLayout(buttons_layout)

    @QtCore.Slot(bool, str)
    def toggle_playlist(self, enabled: bool):
        self.enabled_checkbox.setChecked(enabled)

        p_id = self.playlist.get("id")

        playlist = CONFIG.get_playlist(p_id)

        if playlist is None:
            print(f"Unable to toggle playlist with id {p_id}: Not found on list")
            return

        playlist["enabled"] = enabled

        playlist = CONFIG.set_playlist(playlist)

    @QtCore.Slot(PlaylistData)
    # TODO: Animation download this playlist and cancel button (this has to be blocking but with a worker)
    def _sync_playlist(self, playlist: PlaylistData):
        syncPlaylist(playlist)

    @QtCore.Slot(str)
    def _remove_playlist(self, p_id: str):
        current_playlists = CONFIG.get_all_playlists()

        if current_playlists is None or p_id not in current_playlists:
            print(
                "Unable to remove playlist: List is empty or playlist is not present in it"
            )
            return

        del current_playlists[p_id]

        CONFIG.set_all_playlists(current_playlists)

        self.on_delete.emit()

        self.deleteLater()
