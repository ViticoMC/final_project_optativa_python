import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

from app.config import APP_NAME, APP_TITLE, APP_VERSION, ORGANIZATION


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 700)
        self._build_placeholder()

    def _build_placeholder(self) -> None:
        label = QLabel("FitPlan\n\nFase 0 completada: estructura del proyecto lista.")
        label.setObjectName("placeholder")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
