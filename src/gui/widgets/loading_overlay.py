from PySide6 import QtCore
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
)


class LoadingOverlay(QWidget):
    on_cancel = QtCore.Signal()

    def __init__(self, show_cancel_btn: bool, parent=None):
        super().__init__(parent)

        if show_cancel_btn:
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
            self.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.WindowStaysOnTopHint
            )
            color = QColor(0, 0, 0, 150)
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, color)
            self.setPalette(palette)

        main_layout = QVBoxLayout(self)

        self.container_box = QFrame(self)

        if show_cancel_btn:
            self.container_box.setFrameShape(QFrame.Shape.StyledPanel)
            self.container_box.setFrameShadow(QFrame.Shadow.Raised)

        container_layout = QVBoxLayout(self.container_box)

        if show_cancel_btn:
            container_layout.setContentsMargins(10, 10, 10, 10)

        progress_vbox = QVBoxLayout()

        progress_vbox.setSpacing(0)

        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setMaximum(0)
        progress_bar.setMinimum(0)
        progress_bar.setFixedWidth(200)
        progress_bar.setContentsMargins(0, 0, 0, 0)

        progress_vbox.addWidget(
            progress_bar, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.message_label = QLabel("Loading...")
        self.message_label.setContentsMargins(0, 0, 0, 10)

        progress_vbox.addWidget(
            self.message_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        if show_cancel_btn:
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setFixedWidth(100)
            cancel_btn.clicked.connect(self.cancel)

            progress_vbox.addWidget(
                cancel_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
            )

        container_layout.addLayout(progress_vbox)

        self.container_box.setLayout(container_layout)

        main_layout.addWidget(
            self.container_box, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.setLayout(main_layout)

    @QtCore.Slot(str)
    def set_message(self, message: str):
        self.message_label.setText(message)

    @QtCore.Slot()
    def cancel(self):
        self.on_cancel.emit()
        self.hide()
        self.message_label.setText("Loading...")
