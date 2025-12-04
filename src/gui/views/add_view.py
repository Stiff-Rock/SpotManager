from PySide6 import QtCore, QtGui, QtWidgets
from src.gui.widgets.playlist_card import PlaylistCard
from src.gui.widgets.scroll_playlists_container import ScrollPlaylistsContainer
from src.logic.spotdl_commands import get_user_playlists
from src.utils.config_manager import CONFIG, PlaylistData


class AddView(QtWidgets.QWidget):
    playlist_added_to_list = QtCore.Signal(dict)

    def __init__(self):
        super().__init__()

        self.logic_thread = None
        self.worker = None

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

        # Top input fields
        input_layout = QtWidgets.QHBoxLayout()

        # Username label and input field
        user_id_lbl = QtWidgets.QLabel("User ID")
        self.username_le = QtWidgets.QLineEdit()
        self.username_le.setText(CONFIG.get_username())
        self.username_le.editingFinished.connect(
            lambda: self._search_playlists(self.username_le.text())
        )

        input_layout.addWidget(user_id_lbl)
        input_layout.addWidget(self.username_le)

        self.main_layout.addLayout(input_layout)

        # Playlist scroll list
        self.scroll_playlists_container = ScrollPlaylistsContainer()
        self.main_layout.addWidget(self.scroll_playlists_container)

        self._search_playlists("default")

    @QtCore.Slot(str)
    def _search_playlists(self, username: str):
        if self.logic_thread and self.logic_thread.isRunning():
            print("Previous search is still running, cancelling...")
            return

        self.logic_thread = QtCore.QThread()
        self.worker = SearchPlaylistsWorker(username)
        self.worker.moveToThread(self.logic_thread)

        self.logic_thread.started.connect(self.worker.run)
        self.worker.updated_username.connect(self._update_username)
        self.worker.found_playlist.connect(self._add_playlist_card)

        self.worker.finished.connect(self.logic_thread.quit)

        self.logic_thread.finished.connect(self.worker.deleteLater)
        self.logic_thread.finished.connect(self.logic_thread.deleteLater)

        self.logic_thread.finished.connect(self._cleanup_thread)

        self.scroll_playlists_container.reset_playlist_layout()
        self.logic_thread.start()

    @QtCore.Slot(dict)
    def _add_playlist_card(self, new_playlist: PlaylistData):
        if not self.scroll_playlists_container:
            return

        playlist_card = PlaylistCard("search", new_playlist)
        playlist_card.on_add_playlist.connect(self._add_playlist)
        self.scroll_playlists_container.add_playlist_card(playlist_card)

    @QtCore.Slot(str)
    def _update_username(self, new_username: str):
        self.username_le.setText(new_username)

    @QtCore.Slot(dict)
    def _add_playlist(self, new_playlist: dict):
        if self.logic_thread and self.logic_thread.isRunning():
            print("Previous adding is still running, cancelling...")
            return

        self.logic_thread = QtCore.QThread()
        self.worker = AddPlaylistWorker(new_playlist)
        self.worker.moveToThread(self.logic_thread)

        self.logic_thread.started.connect(self.worker.run)
        self.worker.added_playlist.connect(self.playlist_added_to_list.emit)

        self.worker.finished.connect(self.logic_thread.quit)

        self.logic_thread.finished.connect(self.worker.deleteLater)
        self.logic_thread.finished.connect(self.logic_thread.deleteLater)

        self.logic_thread.finished.connect(self._cleanup_thread)

        self.logic_thread.start()

    def _cleanup_thread(self):
        self.worker = None
        self.logic_thread = None


class SearchPlaylistsWorker(QtCore.QObject):
    updated_username = QtCore.Signal(str)
    found_playlist = QtCore.Signal(PlaylistData)
    progress = QtCore.Signal(int)
    finished = QtCore.Signal()

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._is_cancelled = False

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

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

            get_user_playlists(self.username, self.found_playlist)
        except:
            pass
        finally:
            self.finished.emit()


class AddPlaylistWorker(QtCore.QObject):
    finished = QtCore.Signal()
    added_playlist = QtCore.Signal(PlaylistData)

    def __init__(self, new_playlist):
        super().__init__()
        self.new_playlist: PlaylistData = new_playlist

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

            self.added_playlist.emit(self.new_playlist)
        except:
            pass
        finally:
            self.finished.emit()
