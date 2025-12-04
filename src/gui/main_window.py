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

        manage_view = ManageView()
        add_view = AddView()

        add_view.playlist_added_to_list.connect(manage_view.add_playlist_card)

        tab_widget.addTab(manage_view, "🎵 Manage")
        tab_widget.addTab(add_view, "🔍 Search")

        main_layout.addWidget(tab_widget)
