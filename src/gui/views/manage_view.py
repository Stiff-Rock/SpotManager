import os
import threading
import requests
from PySide6 import QtCore, QtGui, QtWidgets
from src.gui.widgets.loading_overlay import LoadingIndicator
from src.gui.widgets.playlist_card import PlaylistCard
from src.gui.widgets.scroll_playlists_container import ScrollPlaylistsContainer
from src.logic.spotdl_commands import syncPlaylist
from src.utils.cache_manager import CACHE
from src.utils.config_manager import CONFIG, PlaylistData
from src.utils.utils import cleanup_thread


# TODO: MANUALLY ADD BY URL
# BUG: QBasicTimer::stop: Failed. Possibly trying to stop from a different thread


# BUG: After sync all, try to run single sync: Error while synchronizing playlist '✩': There is no current event loop in thread 'Dummy-3'.
# C:\Users\Yago\CodeProjects\SpotManager\src\logic\spotdl_commands.py:260: RuntimeWarning:
# coroutine 'Downloader.pool_download' was never awaited
# print(f"Error while synchronizing playlist '{p_title}': {e}")
# RuntimeWarning: Enable tracemalloc to get the object allocation traceback


class ManageView(QtWidgets.QWidget):
    on_process_start = QtCore.Signal()
    on_process_finish = QtCore.Signal()
    on_update_progress = QtCore.Signal(list)

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

        # Loader
        self.parse_playlist_loading_indicator = LoadingIndicator(
            "LOCAL", hide_cancel_btn=True
        )
        self.parse_playlist_loading_indicator.hide()
        main_layout.addWidget(self.parse_playlist_loading_indicator)

        # Main container
        self.scroll_playlists_container = ScrollPlaylistsContainer()
        main_layout.addWidget(self.scroll_playlists_container)

        # Footer
        footer_layout = QtWidgets.QVBoxLayout()

        sync_btn = QtWidgets.QPushButton("Sync All")
        sync_btn.clicked.connect(self.sync_all_playlists)
        footer_layout.addWidget(sync_btn)

        horizontal_buttons_layout = QtWidgets.QHBoxLayout()
        enable_btn = QtWidgets.QPushButton("Enable All")
        enable_btn.clicked.connect(lambda: self.toggle_all_playlist(True))

        disable_btn = QtWidgets.QPushButton("Disable All")
        disable_btn.clicked.connect(lambda: self.toggle_all_playlist(False))

        horizontal_buttons_layout.addWidget(enable_btn)
        horizontal_buttons_layout.addWidget(disable_btn)

        footer_layout.addLayout(horizontal_buttons_layout)

        show_folder_btn = QtWidgets.QPushButton("Show playlists folder")
        show_folder_btn.clicked.connect(self.open_playlists_folder)
        footer_layout.addWidget(show_folder_btn)

        main_layout.addLayout(footer_layout)

        self.parse_playlists()

    def parse_playlists(self):
        if self._logic_thread and self._logic_thread.isRunning():
            print("Can't parse playlists, logic thread is currently busy")
            return

        self._logic_thread = QtCore.QThread()
        self.worker = ParsePlaylistsWorker()

        self.worker.moveToThread(self._logic_thread)

        self._logic_thread.started.connect(self.worker.run)
        self._logic_thread.finished.connect(
            lambda: cleanup_thread(self, "worker", "_logic_thread")
        )

        self.worker.finished.connect(self._logic_thread.quit)

        # Custom Signals
        self.worker.on_add_playlist.connect(self.add_playlist_card)
        self.worker.progress.connect(self.parse_playlist_loading_indicator.set_message)
        self.worker.finished.connect(
            lambda: self.parse_playlist_loading_indicator.hide()
        )

        self._logic_thread.start()
        self.parse_playlist_loading_indicator.show()

    @QtCore.Slot()
    def toggle_all_playlist(self, enabled: bool):
        for card in self.playlist_cards:
            if isinstance(card, PlaylistCard):
                card.toggle_playlist(enabled)

    @QtCore.Slot()
    def sync_all_playlists(self):
        if self._logic_thread and self._logic_thread.isRunning():
            print(
                "Can't sync all playlists, another logic thread is already running in the manage_view"
            )
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
        self.worker.progress.connect(self.on_update_progress.emit)
        self.worker.finished.connect(self.on_process_finish.emit)

        self._logic_thread.start()
        self.on_process_start.emit()

    @QtCore.Slot(PlaylistData, bytes)
    def add_playlist_card(self, new_playlist: PlaylistData, cover_bytes: bytes):
        callback = self.scroll_playlists_container.change_playlist_priority

        new_card = PlaylistCard(
            "manage",
            new_playlist,
            cover_bytes,
            callback,
        )

        p_id = new_playlist.get("id")
        CACHE.save_cover(cover_bytes, p_id)

        new_card.on_sync_start.connect(self.on_process_start.emit)
        new_card.on_sync_progress_update.connect(self.on_update_progress.emit)
        new_card.on_sync_finish.connect(self.on_process_finish.emit)

        new_card.on_delete.connect(
            lambda card=new_card: self.playlist_cards.remove(card)
        )
        self.playlist_cards.append(new_card)
        insertion_index = self.scroll_playlists_container.add_playlist_card(new_card)

        if insertion_index is not None:
            CONFIG.set_playlist_priority(p_id, insertion_index)

    @QtCore.Slot()
    def open_playlists_folder(self):
        os.startfile(CONFIG.get_playlists_path())


class SyncAllPlaylistsWorker(QtCore.QObject):
    finished = QtCore.Signal()
    progress = QtCore.Signal(list)

    def __init__(self):
        super().__init__()
        self.cancel_event = threading.Event()

    @QtCore.Slot()
    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            amount = sum(
                playlist.get("enabled", False)
                for playlist in CONFIG.get_all_playlists().values()
            )

            index = 0

            for current_playlist in CONFIG.get_all_playlists().values():
                if self.cancel_event and self.cancel_event.is_set():
                    return

                if current_playlist.get("enabled"):
                    index += 1
                    syncPlaylist(
                        current_playlist,
                        amount,
                        index,
                        self.progress,
                        self.cancel_event,
                    )
        except Exception as e:
            print(f"An unexpected error occurred during playlist sync: {e}")
        finally:
            self.finished.emit()


class ParsePlaylistsWorker(QtCore.QObject):
    finished = QtCore.Signal()
    progress = QtCore.Signal(list)
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
                p_id = playlist.get("id")
                cover_bytes = CACHE.get_cover(p_id)

                if not cover_bytes:
                    response = requests.get(playlist.get("cover_url"))

                    if response.status_code == 200:
                        cover_bytes = response.content or bytes()
                        CACHE.save_cover(cover_bytes, p_id)
                    else:
                        cover_bytes = bytes()

                self.on_add_playlist.emit(playlist, cover_bytes)
                self.progress.emit(
                    [f"Loading playlist... {i + 1}/{len(current_playlists)}"]
                )
        except Exception as e:
            print(f"An unexpected error occurred during playlist processing: {e}")
        finally:
            self.finished.emit()
