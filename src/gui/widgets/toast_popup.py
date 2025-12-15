from PySide6 import QtCore
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class ToastPopUp(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowFlags(
            QtCore.Qt.WindowType.ToolTip
            | QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setStyleSheet("""
            background-color: rgba(255, 255, 200, 240);  /* Amarillo suave y transparente */
            color: black;                                /* Texto oscuro para contraste */
            padding: 5px 10px;                           /* Reducir el relleno */
            border-radius: 4px;                          /* Borde más pequeño */
        """)

        main_layout = QVBoxLayout(self)
        self.message_label = QLabel()
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.message_label)

        self.adjustSize()
        self.hide()

    @QtCore.Slot(str)
    def display(self, message: str, duration_ms: int = 3000):
        self.message_label.setText(message)
        self.adjustSize()

        cursor_pos = QCursor.pos()

        x = cursor_pos.x()
        y = cursor_pos.y()

        self.move(x, y)

        self.show()

        QtCore.QTimer.singleShot(duration_ms, self.close)
