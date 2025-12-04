from PySide6 import QtWidgets

from src.gui.widgets.playlist_card import PlaylistCard


class ScrollPlaylistsContainer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QtWidgets.QVBoxLayout(self)

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

        self.playlists_container_layout.insertWidget(
            self.playlists_container_layout.count() - 1, playlist_card
        )
