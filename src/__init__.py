import sys
from PySide6 import QtWidgets
import window

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = window.SpotWidget()
    widget.show()

    sys.exit(app.exec())
