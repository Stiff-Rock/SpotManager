import enum
import requests
from PySide6 import QtCore, QtGui, QtWidgets
from src.gui.widgets.loading_overlay import LoadingOverlay
from src.gui.widgets.playlist_card import PlaylistCard
from src.gui.widgets.scroll_playlists_container import ScrollPlaylistsContainer
from src.logic.spotdl_commands import syncPlaylist
from src.utils.config_manager import CONFIG, PlaylistData
from src.utils.utils import cleanup_thread


class ManageView(QtWidgets.QWidget):
    on_process_start = QtCore.Signal()
    on_process_finish = QtCore.Signal()
    on_update_progress = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

        self.playlist_cards = []

        self._logic_thread = None
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

        self.local_loading_overlay = LoadingOverlay(False)
        self.local_loading_overlay.hide()
        main_layout.addWidget(self.local_loading_overlay)

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

    # TODO: CACHE THE ITEMS SO NO NEED TO RE-MAKE
    def parse_playlists(self):
        if self._logic_thread and self._logic_thread.isRunning():
            return

        self._logic_thread = QtCore.QThread()
        self.worker = AddPlaylistCardsWorker()

        self.worker.moveToThread(self._logic_thread)

        self._logic_thread.started.connect(self.worker.run)
        self._logic_thread.finished.connect(
            lambda: cleanup_thread(self, "worker", "_logic_thread")
        )

        self.worker.finished.connect(self._logic_thread.quit)

        # Custom Signals
        self.worker.on_add_playlist.connect(self.add_playlist_card)
        self.worker.progress.connect(self.local_loading_overlay.set_message)
        self.worker.finished.connect(lambda: self.local_loading_overlay.hide())

        self._logic_thread.start()
        self.local_loading_overlay.show()

    @QtCore.Slot()
    def toggle_all_playlist(self, enabled: bool):
        for card in self.playlist_cards:
            if isinstance(card, PlaylistCard):
                card.toggle_playlist(enabled)

    @QtCore.Slot()
    def sync_all_playlists(self):
        if self._logic_thread and self._logic_thread.isRunning():
            return

        self._logic_thread = QtCore.QThread()

        self.worker = SyncAllPlaylistsWorker()

        self.worker.moveToThread(self._logic_thread)

        self._logic_thread.started.connect(self.worker.run)
        self._logic_thread.finished.connect(
            lambda: cleanup_thread(self, "worker", "_logic_thread")
        )

        self.worker.finished.connect(self._logic_thread.quit)

        # Custom Signals
        self.enabled_playlist_count = sum(
            playlist.get("enabled", False)
            for playlist in CONFIG.get_all_playlists().values()
        )

        self.worker.progress.connect(self._update_sync_loading_msg)
        self.worker.finished.connect(self.on_process_finish.emit)

        self._logic_thread.start()
        self.on_process_start.emit()

    QtCore.Slot(str, int)

    def _update_sync_loading_msg(self, msg: str, p_i: int):
        self.on_update_progress.emit(f"({p_i}/{self.enabled_playlist_count}) {msg}")

    @QtCore.Slot(PlaylistData, bytes)
    def add_playlist_card(self, new_playlist: PlaylistData, cover_bytes: bytes):
        new_card = PlaylistCard("manage", new_playlist, cover_bytes)
        new_card.on_delete.connect(
            lambda card=new_card: self.playlist_cards.remove(card)
        )
        self.playlist_cards.append(new_card)
        self.scroll_playlists_container.add_playlist_card(new_card)


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
            counter = 0
            for playlist in CONFIG.get_all_playlists().values():
                if playlist.get("enabled"):
                    counter += 1
                    syncPlaylist(playlist, self.progress, counter)
                    # TODO: IMPROVE THE MESSAGE AND THE LOADER LAYOUT
        except:
            pass
        finally:
            self.finished.emit()


class AddPlaylistCardsWorker(QtCore.QObject):
    finished = QtCore.Signal()
    progress = QtCore.Signal(str)
    on_add_playlist = QtCore.Signal(PlaylistData, bytes)

    def __init__(self):
        super().__init__()

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            current_playlists = CONFIG.get_all_playlists()

            if current_playlists is None:
                print("Unable to show saved playlists: Non existent key on json file")
                return

            for i, playlist in enumerate(current_playlists.values()):
                response = requests.get(playlist.get("cover_url"))

                cover_bytes = None
                if response.status_code == 200:
                    cover_bytes = response.content or bytes()
                else:
                    cover_bytes = bytes()

                self.on_add_playlist.emit(playlist, cover_bytes)
                self.progress.emit(
                    f"Loading playlist... {i + 1}/{len(current_playlists)}"
                )
        except:
            pass
        finally:
            self.finished.emit()
