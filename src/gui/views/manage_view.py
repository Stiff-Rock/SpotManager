from PySide6 import QtCore, QtGui, QtWidgets
from src.gui.widgets.playlist_card import PlaylistCard
from src.gui.widgets.scroll_playlists_container import ScrollPlaylistsContainer
from src.logic.spotdl_commands import syncPlaylist
from src.utils.config_manager import CONFIG, PlaylistData


class ManageView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.playlist_cards = []

        self.logic_thread = None
        self.worker = None

        main_layout = QtWidgets.QVBoxLayout(self)

        # Header
        header_lbl = QtWidgets.QLabel(
            "<b>MANAGE PLAYLISTS</b>", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        font = QtGui.QFont()
        font.setPointSize(18)
        header_lbl.setFont(font)
        main_layout.addWidget(header_lbl)

        self.scroll_playlists_container = ScrollPlaylistsContainer()
        main_layout.addWidget(self.scroll_playlists_container)

        # Footer
        footer_layout = QtWidgets.QVBoxLayout()

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

        main_layout.addLayout(footer_layout)

        self.parse_playlists()

    def parse_playlists(self):
        current_playlists = CONFIG.get_all_playlists()

        if current_playlists is None:
            print("Unable to show saved playlists: Non existent key on json file")
            return

        for playlist in current_playlists.values():
            self.add_playlist_card(playlist)

    @QtCore.Slot()
    def toggle_all_playlist(self, enabled: bool):
        for card in self.playlist_cards:
            if isinstance(card, PlaylistCard):
                card.toggle_playlist(enabled)

    # TODO: Animation download this playlist and cancel button (this has to be blocking but with a worker)
    @QtCore.Slot()
    def sync_all_playlists(self):
        if self.logic_thread and self.logic_thread.isRunning():
            print("Previous all sync is still running, cancelling...")
            return

        self.logic_thread = QtCore.QThread()
        self.worker = SyncAllPlaylistsWorker()
        self.worker.moveToThread(self.logic_thread)

        self.logic_thread.started.connect(self.worker.run)

        self.worker.progress.connect(self.update_progress_bar)

        self.worker.finished.connect(self.logic_thread.quit)

        self.logic_thread.finished.connect(self.worker.deleteLater)
        self.logic_thread.finished.connect(self.logic_thread.deleteLater)

        self.logic_thread.finished.connect(self._cleanup_thread)

        self.synching_playlist_count = sum(
            playlist.get("enabled", False)
            for playlist in CONFIG.get_all_playlists().values()
        )

        self.logic_thread.start()

    @QtCore.Slot(int)
    def update_progress_bar(self, song_name: str, progress: int):
        print(f"Downloading {song_name}...: {progress}%")

    @QtCore.Slot(dict)
    def add_playlist_card(self, new_playlist: PlaylistData):
        new_card = PlaylistCard("manage", new_playlist)
        new_card.on_delete.connect(
            lambda card=new_card: self.playlist_cards.remove(card)
        )
        self.playlist_cards.append(new_card)
        self.scroll_playlists_container.add_playlist_card(new_card)

    def _cleanup_thread(self):
        self.worker = None
        self.logic_thread = None


# TODO: PROGRESS HAS TO ALSO REFLECT WHICH PLAYLIST IS CURRENTLY BEING SYNCHED
class SyncAllPlaylistsWorker(QtCore.QObject):
    finished = QtCore.Signal()
    progress = QtCore.Signal(str, int)

    def __init__(self):
        super().__init__()

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            for playlist in CONFIG.get_all_playlists().values():
                if playlist.get("enabled"):
                    syncPlaylist(playlist, self.progress)
        except:
            pass
        finally:
            self.finished.emit()
