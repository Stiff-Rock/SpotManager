from PySide6 import QtWidgets
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6.QtGui import QIcon
from src.gui.views.add_view import AddView
from src.gui.views.manage_view import ManageView
from src.gui.widgets.loading_overlay import LoadingOverlay


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.resize(850, 600)
        self.setWindowTitle("SpotManager")

        icon_path = "resources/app_icon.png"
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        main_layout = QtWidgets.QVBoxLayout(self)

        tab_widget = QtWidgets.QTabWidget()

        self.loading_overlay = LoadingOverlay(True, parent=self)
        self.loading_overlay.on_cancel.connect(self.cancel_process)
        self.loading_overlay.hide()

        self.manage_view = ManageView()
        self.manage_view.on_process_start.connect(lambda: self.loading_overlay.show())
        self.manage_view.on_update_progress.connect(self.loading_overlay.set_message)
        self.manage_view.on_process_finish.connect(lambda: self.loading_overlay.hide())

        self.add_view = AddView()
        self.add_view.playlist_added_to_list.connect(self.manage_view.add_playlist_card)

        tab_widget.addTab(self.manage_view, "🎵 Manage")
        tab_widget.addTab(self.add_view, "🔍 Search")

        main_layout.addWidget(tab_widget)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        self.loading_overlay.resize(self.size())
        self.loading_overlay.move(0, 0)
        self.loading_overlay.raise_()
        super().resizeEvent(event)

    @QtCore.Slot()
    def cancel_process(self):
        if self.manage_view.worker:
            self.manage_view.worker.cancel()
            print("Cancelling manage_view worker")

        if self.add_view.worker:
            self.add_view.worker.cancel()
            print("Cancelling add_view worker")
