import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from app.config import APP_NAME, APP_VERSION, ORGANIZATION
from services.container import AppServices
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService
from ui.main_window import MainWindow


def crear_servicios() -> AppServices:
    csv_service = CsvService()
    return AppServices(
        rutinas=RutinaService(csv_service),
        ejercicios=EjercicioService(csv_service),
    )


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")

    window = MainWindow(crear_servicios())
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
