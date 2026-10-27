import sys

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QApplication

from app.config import APP_NAME, APP_VERSION, ORGANIZATION
from services.comida_personal_service import ComidaPersonalService
from services.container import AppServices
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.export_service import ExportService
from services.nutricion_service import NutricionService
from services.plantilla_service import PlantillaService
from services.rutina_service import RutinaService
from ui.main_window import MainWindow
from ui.styles import aplicar_estilo


def crear_servicios() -> AppServices:
    csv_service = CsvService()
    rutinas = RutinaService(csv_service)
    ejercicios = EjercicioService(csv_service)
    nutricion = NutricionService(csv_service)
    return AppServices(
        rutinas=rutinas,
        ejercicios=ejercicios,
        nutricion=nutricion,
        estadisticas=EstadisticaService(),
        exportacion=ExportService(csv_service),
        plantillas=PlantillaService(csv_service, ejercicios, rutinas),
        comidas_personales=ComidaPersonalService(csv_service, nutricion),
    )


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    aplicar_estilo(app)

    window = MainWindow(crear_servicios(), settings=QSettings())
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
