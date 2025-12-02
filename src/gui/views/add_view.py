import json
from PySide6 import QtCore, QtGui, QtWidgets
from src.logic.spotdl_commands import get_user_playlists
from src.utils.config_manager import CONFIG
from src.utils.utils import PLAYLISTS_JSON_PATH, clear_layout


class AddView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        add_layout = QtWidgets.QVBoxLayout(self)

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
        add_layout.addLayout(header_layout)

        # Top input fields
        input_layout = QtWidgets.QHBoxLayout()

        # Username label and input field
        username_lbl = QtWidgets.QLabel("Username")
        username_le = QtWidgets.QLineEdit()
        username_le.setText(CONFIG.get("username"))
        self.search_playlists(username_le.text())
        username_le.editingFinished.connect(
            lambda: self.search_playlists(username_le.text())
        )

        input_layout.addWidget(username_lbl)
        input_layout.addWidget(username_le)

        add_layout.addLayout(input_layout)

        # Playlist list
        playlists_container_widget = QtWidgets.QWidget()
        self.playlists_container_layout = QtWidgets.QVBoxLayout(
            playlists_container_widget
        )

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(playlists_container_widget)

        add_layout.addWidget(scroll_area)

        # Footer
        footer_layout = QtWidgets.QVBoxLayout()
        footer_layout.setContentsMargins(0, 20, 0, 20)

        """
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
        """

        add_layout.addLayout(footer_layout)

    # TODO: THE SYNC OPERATIONS ARE BLOCKING ONES

    @QtCore.Slot(str)
    def search_playlists(self, username: str | None):
        clear_layout(self.playlists_container_layout)

        with open(PLAYLISTS_JSON_PATH, "r+") as file:
            try:
                self.data = json.load(file)
            except json.JSONDecodeError:
                self.data = {}
                json.dump(self.data, file, indent=2)
            except FileNotFoundError:
                print(f"Error: {PLAYLISTS_JSON_PATH} not found.")
                return

            if username is None:
                if not self.data["username"]:
                    # Write a default value
                    self.data["username"] = "Spotify"
                    file.seek(0)
                    json.dump(self.data, file, indent=2)
                else:
                    username = self.data["username"]
            else:
                # Write new value
                self.data["username"] = username
                file.seek(0)
                json.dump(self.data, file, indent=2)

            if not username:
                print("Could not find playlists: no username provided")
                return

            user_playlists = get_user_playlists(username)

            if not user_playlists:
                print(f"No playlists found for user id {username}")
                return

            for playlist in user_playlists:
                title = playlist.get("title", "N/A")
                url = playlist.get("url", "#")

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
                add_button = QtWidgets.QPushButton("Add")
                add_button.clicked.connect(self.add_playlist)

                buttons_layout.addWidget(add_button, stretch=4)

                # Sync playlist button
                """
                sync_btn = QtWidgets.QPushButton("Sync Playlist")
                sync_btn.clicked.connect(
                    lambda _, p_data=playlist: self.sync_playlist(p_data)
                )
                buttons_layout.addWidget(sync_btn, stretch=1)

                playlist_layout.addLayout(buttons_layout)
                """

                self.playlists_container_layout.addWidget(playlist_container)

    def add_playlist(self):
        print("ADDING")
