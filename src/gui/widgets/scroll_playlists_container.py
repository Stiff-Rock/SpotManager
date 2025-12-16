from PySide6 import QtWidgets

from src.gui.widgets.playlist_card import PlaylistCard


class ScrollPlaylistsContainer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.playlist_cards: list[PlaylistCard] = []

        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Search bar and search button
        seach_layout = QtWidgets.QHBoxLayout()

        self.playlist_le = QtWidgets.QLineEdit()
        self.playlist_le.textChanged.connect(
            lambda: self.filter_by_title(self.playlist_le.text())
        )
        self.playlist_le.setPlaceholderText("Filter by playlist name")
        seach_layout.addWidget(self.playlist_le)

        search_song_btn = QtWidgets.QPushButton("Search Playlist")
        search_song_btn.clicked.connect(
            lambda: self.filter_by_title(self.playlist_le.text())
        )
        seach_layout.addWidget(search_song_btn)
        self.main_layout.addLayout(seach_layout)

        # Scroll container
        self.playlists_container_widget = None
        self.playlists_container_layout = None
        self.vertical_spacer = None

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.main_layout.addWidget(self.scroll_area)

        self.reset_playlist_layout()

    def reset_playlist_layout(self):
        if self.playlists_container_widget:
            self.playlists_container_widget.deleteLater()
            self.playlists_container_widget = None

        self.playlists_container_widget = QtWidgets.QWidget()

        self.playlists_container_layout = QtWidgets.QVBoxLayout(
            self.playlists_container_widget
        )
        self.playlists_container_layout.setContentsMargins(0, 0, 0, 0)
        self.playlists_container_layout.setSpacing(0)

        self.vertical_spacer = QtWidgets.QSpacerItem(
            0,
            0,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.playlists_container_layout.addItem(self.vertical_spacer)

        self.scroll_area.setWidget(self.playlists_container_widget)

    def add_playlist_card(self, playlist_card: PlaylistCard):
        if not self.playlists_container_layout:
            return

        insertion_index = self.playlists_container_layout.count() - 1

        # Always add on top
        self.playlists_container_layout.insertWidget(insertion_index, playlist_card)
        self.playlist_cards.append(playlist_card)

        return insertion_index

    def filter_by_title(self, title_filter: str):
        for card in self.playlist_cards:
            title = card.playlist.get("title")
            if not title_filter or title_filter.lower() in title.lower():
                card.show()
            else:
                card.hide()
