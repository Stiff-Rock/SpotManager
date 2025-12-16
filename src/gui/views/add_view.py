import threading
from src.gui.widgets.loading_overlay import LoadingIndicator
from PySide6 import QtCore, QtGui, QtWidgets
from src.gui.widgets.playlist_card import PlaylistCard
from src.gui.widgets.scroll_playlists_container import ScrollPlaylistsContainer
from src.logic.spotdl_commands import get_user_playlists
from src.utils.config_manager import CONFIG, PlaylistData
from src.utils.utils import cleanup_thread


class AddView(QtWidgets.QWidget):
    playlist_added_to_list = QtCore.Signal(PlaylistData, bytes)

    def __init__(self):
        super().__init__()

        self._search_logic_thread = None
        self.search_worker = None

        self._add_logic_thread = None
        self.add_worker = None

        self.main_layout = QtWidgets.QVBoxLayout(self)

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
        self.main_layout.addLayout(header_layout)

        # Loader
        self.search_playlist_loading_indicator = LoadingIndicator("LOCAL")
        self.search_playlist_loading_indicator.on_cancel.connect(self.cancel_search)
        self.search_playlist_loading_indicator.hide()
        self.main_layout.addWidget(self.search_playlist_loading_indicator)

        # Username label, input field and search button
        input_layout = QtWidgets.QHBoxLayout()

        self.username_le = QtWidgets.QLineEdit()
        self.username_le.setText(CONFIG.get_username())
        self.username_le.setPlaceholderText("User ID")
        self.username_le.editingFinished.connect(
            lambda: self._search_user_playlists(self.username_le.text())
        )
        self.username_le.setPlaceholderText("Spotify User Id")
        input_layout.addWidget(self.username_le)

        search_user_btn = QtWidgets.QPushButton("Load")
        search_user_btn.clicked.connect(
            lambda: self._search_user_playlists(self.username_le.text())
        )
        input_layout.addWidget(search_user_btn)

        self.main_layout.addLayout(input_layout)

        # Playlist scroll list
        self.scroll_playlists_container = ScrollPlaylistsContainer()
        self.main_layout.addWidget(self.scroll_playlists_container)

        self._search_user_playlists("default")

    @QtCore.Slot(str)
    def _search_user_playlists(self, username: str):
        if self._search_logic_thread and self._search_logic_thread.isRunning():
            print("Can't search playlists, logic thread is currently busy")
            return

        self._search_logic_thread = QtCore.QThread()
        self.search_worker = SearchPlaylistsWorker(username)

        self.search_worker.moveToThread(self._search_logic_thread)

        self._search_logic_thread.started.connect(self.search_worker.run)
        self._search_logic_thread.finished.connect(
            lambda: cleanup_thread(self, "search_worker", "_search_logic_thread")
        )

        self.search_worker.finished.connect(self._search_logic_thread.quit)

        # Custom Signals
        self.search_worker.updated_username.connect(self._update_username)
        self.search_worker.found_playlist.connect(self._add_search_playlist_card)
        self.search_worker.progress.connect(
            self.search_playlist_loading_indicator.set_message
        )
        self.search_worker.finished.connect(self.search_playlist_loading_indicator.hide)

        self.scroll_playlists_container.reset_playlist_layout()
        self.search_playlist_loading_indicator.show()
        self._search_logic_thread.start()

    @QtCore.Slot()
    def cancel_search(self):
        if self.search_worker is not None:
            self.search_worker.cancel()

    @QtCore.Slot(dict)
    def _add_search_playlist_card(self, new_playlist: PlaylistData, cover_bytes: bytes):
        if not self.scroll_playlists_container:
            return

        callback = self.scroll_playlists_container.change_playlist_priority

        playlist_card = PlaylistCard("search", new_playlist, cover_bytes, callback)
        playlist_card.on_add_playlist.connect(self._add_playlist_to_collection)
        self.scroll_playlists_container.add_playlist_card(playlist_card)

    @QtCore.Slot(str)
    def _update_username(self, new_username: str):
        self.username_le.setText(new_username)

    @QtCore.Slot(dict)
    def _add_playlist_to_collection(
        self, new_playlist: PlaylistData, cover_bytes: bytes
    ):
        if self._add_logic_thread and self._add_logic_thread.isRunning():
            print("Can't add plylist, logic thread is currently busy")
            return

        self._add_logic_thread = QtCore.QThread()
        self.add_worker = AddPlaylistToCollectionWorker(new_playlist, cover_bytes)

        self.add_worker.moveToThread(self._add_logic_thread)

        self._add_logic_thread.started.connect(self.add_worker.run)
        self._add_logic_thread.finished.connect(
            lambda: cleanup_thread(self, "add_worker", "_add_logic_thread")
        )

        self.add_worker.finished.connect(self._add_logic_thread.quit)

        # Custom Signals
        self.add_worker.added_playlist_to_collection.connect(
            self.playlist_added_to_list.emit
        )

        self._add_logic_thread.start()


class SearchPlaylistsWorker(QtCore.QObject):
    updated_username = QtCore.Signal(str)
    found_playlist = QtCore.Signal(PlaylistData, bytes)
    progress = QtCore.Signal(list)
    finished = QtCore.Signal()

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.cancel_event = threading.Event()

    @QtCore.Slot()
    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            if not self.username:
                self.finished.emit()
                return
            elif self.username == "default":
                if not CONFIG.get_username():
                    # Write a default value
                    CONFIG.set_username("Spotify")
                    self.updated_username.emit(self.username)
                else:
                    self.username = CONFIG.get_username()
            else:
                # Write new value
                CONFIG.set_username(self.username)

            if not self.username:
                print("Could not find playlists: no username provided")
                self.finished.emit()
                return

            get_user_playlists(
                self.username, self.found_playlist, self.progress, self.cancel_event
            )
        except:
            pass
        finally:
            self.finished.emit()


class AddPlaylistToCollectionWorker(QtCore.QObject):
    finished = QtCore.Signal()
    added_playlist_to_collection = QtCore.Signal(PlaylistData, bytes)

    def __init__(self, new_playlist: PlaylistData, cover_bytes: bytes):
        super().__init__()
        self.new_playlist = new_playlist
        self.cover_bytes = cover_bytes

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            current_playlists = CONFIG.get_all_playlists()

            p_id = self.new_playlist.get("id")

            if current_playlists is None:
                print("Unable to add playlists: Non existent key on json file")
                self.finished.emit()
                return

            if p_id in current_playlists:
                print(f"Playlist with id {p_id} is already present on list")
                self.finished.emit()
                return

            self.new_playlist["enabled"] = True

            CONFIG.set_playlist(self.new_playlist)

            self.added_playlist_to_collection.emit(self.new_playlist, self.cover_bytes)
        except Exception as e:
            print(f"Error while adding playlist to collection: {e}")
        finally:
            self.finished.emit()
