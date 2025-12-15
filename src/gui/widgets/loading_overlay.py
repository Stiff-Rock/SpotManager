from typing import Literal
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
from spotdl import Union

LOADER_TYPE = Union[Literal["LOCAL"], Literal["OVERLAY"]]


class LoadingIndicator(QWidget):
    on_cancel = QtCore.Signal()

    def __init__(self, type: LOADER_TYPE, parent=None):
        super().__init__(parent)
        self.type = type

        # Window properties
        if type == "OVERLAY":
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

        # Frame configuration
        if type == "OVERLAY":
            self.container_box.setFrameShape(QFrame.Shape.StyledPanel)
            self.container_box.setFrameShadow(QFrame.Shadow.Raised)

        container_layout = QVBoxLayout(self.container_box)

        if type == "LOCAL":
            container_layout.setContentsMargins(10, 10, 10, 10)

        progress_vbox = QVBoxLayout()
        progress_vbox.setSpacing(0)

        # Messages layout
        messages_layout = QVBoxLayout()

        if type == "OVERLAY":
            message_title = QLabel("Sync in progress...")
            message_title.setContentsMargins(0, 0, 0, 10)
            message_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            messages_layout.addWidget(message_title)

            self.message_label_1 = QLabel("Playlist: None")
            self.message_label_1.setContentsMargins(0, 0, 0, 10)
            self.message_label_1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            messages_layout.addWidget(self.message_label_1)

        self.message_label_2 = QLabel("Loading...")
        self.message_label_2.setContentsMargins(0, 0, 0, 10)
        self.message_label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        messages_layout.addWidget(self.message_label_2)

        progress_vbox.addLayout(messages_layout)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setMaximum(0)
        progress_bar.setMinimum(0)
        progress_bar.setFixedWidth(200)
        progress_bar.setContentsMargins(0, 0, 0, 0)
        progress_vbox.addWidget(
            progress_bar, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.cancel)

        progress_vbox.addWidget(
            self.cancel_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        container_layout.addLayout(progress_vbox)

        self.container_box.setLayout(container_layout)

        main_layout.addWidget(
            self.container_box, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.setLayout(main_layout)

    @QtCore.Slot(list)
    def set_message(self, message_parts: list[str]):
        if self.type == "LOCAL":
            self.message_label_2.setText(message_parts[0])
        else:
            self.message_label_1.setText(message_parts[0])
            self.message_label_2.setText(message_parts[1])

    @QtCore.Slot()
    def toggle_canncel_btn(self, show: bool):
        self.cancel_btn.setVisible(show)

    @QtCore.Slot()
    def cancel(self):
        self.on_cancel.emit()
        self.message_label_2.setText("Cancelling...")
