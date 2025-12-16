import threading
from typing import Literal
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QPixmap
from src.logic.spotdl_commands import syncPlaylist
from src.utils.config_manager import CONFIG, PlaylistData
from src.utils.utils import cleanup_thread

CARD_MARGIN = 10
MAX_HEIGHT = 130
COVER_DIMS = 90

CardType = Literal["search", "manage"]


class PlaylistCard(QtWidgets.QWidget):
    on_add_playlist = QtCore.Signal(PlaylistData, bytes)
    on_sync_start = QtCore.Signal()
    on_sync_progress_update = QtCore.Signal(list)
    on_sync_finish = QtCore.Signal()
    on_delete = QtCore.Signal()

    def __init__(self, type: CardType, new_playlist: PlaylistData, cover_bytes: bytes):
        super().__init__()

        self.setMaximumHeight(MAX_HEIGHT)

        self._logic_thread = None
        self.worker = None

        self.playlist = new_playlist

        title = new_playlist.get("title", "N/A")
        total_tracks = new_playlist.get("total_tracks", "-1")
        url = self.playlist.get("url", "#")
        p_id = new_playlist.get("id")

        top_layout = QtWidgets.QVBoxLayout(self)
        top_layout.setContentsMargins(
            CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN
        )

        playlist_card = QtWidgets.QFrame()
        playlist_card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        top_layout.addWidget(playlist_card)

        horizonal_layout = QtWidgets.QHBoxLayout(playlist_card)

        # Cover Image Label
        image_label = QtWidgets.QLabel()
        image_label.setScaledContents(True)
        image_label.setFixedSize(COVER_DIMS, COVER_DIMS)
        image_label.setScaledContents(True)

        cover_img = QPixmap()
        cover_img.loadFromData(cover_bytes)
        image_label.setPixmap(cover_img)

        horizonal_layout.addWidget(image_label)

        # Playlist Info Layout
        playlist_layout = QtWidgets.QVBoxLayout()

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

        horizonal_layout.addLayout(playlist_layout)

        if type == "search":
            # Add playlist button
            add_btn = QtWidgets.QPushButton("Add")
            add_btn.clicked.connect(
                lambda _, p=self.playlist, b=cover_bytes: self.on_add_playlist.emit(
                    p, b
                )
            )
            playlist_layout.addWidget(add_btn)
        else:
            buttons_layout = QtWidgets.QHBoxLayout()

            self.enabled_checkbox = QtWidgets.QCheckBox("Enabled: ")
            self.enabled_checkbox.setChecked(new_playlist.get("enabled"))
            self.enabled_checkbox.toggled.connect(self.toggle_playlist)
            buttons_layout.addWidget(self.enabled_checkbox, stretch=8)

            priority_up_btn = QtWidgets.QPushButton("↑")
            priority_up_btn.clicked.connect(
                lambda _, p=new_playlist: self._change_playlist_priority(p, -1)
            )
            buttons_layout.addWidget(priority_up_btn, stretch=1)

            priority_down_btn = QtWidgets.QPushButton("↓")
            priority_down_btn.clicked.connect(
                lambda _, p=new_playlist: self._change_playlist_priority(p, 1)
            )
            buttons_layout.addWidget(priority_down_btn, stretch=1)

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
    def _sync_playlist(self, playlist: PlaylistData):
        if self._logic_thread and self._logic_thread.isRunning():
            print("Previous sync is still running, cancelling...")
            return

        self._logic_thread = QtCore.QThread()
        self.worker = SyncPlaylistsWorker(playlist)

        self.worker.moveToThread(self._logic_thread)

        self._logic_thread.started.connect(self.worker.run)
        self._logic_thread.finished.connect(
            lambda: cleanup_thread(self, "worker", "_logic_thread")
        )

        self.worker.finished.connect(self._logic_thread.quit)

        # Custom Signals
        self.worker.progress.connect(self.on_sync_progress_update.emit)
        self.worker.finished.connect(self.on_sync_finish.emit)

        self.synching_playlist_count = sum(
            playlist.get("enabled", False)
            for playlist in CONFIG.get_all_playlists().values()
        )

        self.on_sync_start.emit()
        self._logic_thread.start()

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

    @QtCore.Slot()
    def _change_playlist_priority(self, playlist: PlaylistData, change: int):
        old_priority = playlist.get("priority")
        new_priority = old_priority + change

        if new_priority <= 0:
            print(f"Ignoring priority change of playlist {playlist.get('title')}")
            return

        CONFIG.set_playlist_priority(playlist.get("id"), new_priority)

        parent_widget = self.parent()
        children_list = parent_widget.children()
        child_to_move = children_list.pop(old_priority)
        children_list.insert(new_priority, child_to_move)

        print(f"parent_widget {parent_widget}")


class SyncPlaylistsWorker(QtCore.QObject):
    finished = QtCore.Signal()
    progress = QtCore.Signal(list)

    def __init__(self, playlist: PlaylistData):
        super().__init__()
        self.playlist = playlist
        self.cancel_event = threading.Event()

    @QtCore.Slot()
    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            syncPlaylist(self.playlist, 1, 1, self.progress, self.cancel_event)
        except Exception as e:
            print(
                f"An error occurred while synchronizing the playlist '{self.playlist.get('title')}': {e}"
            )
        finally:
            self.finished.emit()
