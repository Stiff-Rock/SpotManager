from PySide6 import QtWidgets
from src.gui.views.add_view import AddView
from src.gui.views.manage_view import ManageView


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.resize(850, 600)
        self.setWindowTitle("SpotManager")

        main_layout = QtWidgets.QVBoxLayout(self)

        tab_widget = QtWidgets.QTabWidget()

        playlist_view = AddView()
        search_view = ManageView()

        tab_widget.addTab(playlist_view, "🎵 Add Playlists")
        tab_widget.addTab(search_view, "🔍 Manage Settings")

        main_layout.addWidget(tab_widget)
