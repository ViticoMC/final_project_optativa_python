from pathlib import Path

from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from app.config import APP_TITLE, APP_VERSION, DATA_DIR
from app.exceptions import FitPlanError
from services.rutina_service import RutinaService
from ui.widgets.rutinas_tab import RutinasTab


class MainWindow(QMainWindow):
    def __init__(
        self,
        rutina_service: RutinaService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.rutina_service = rutina_service
        self._ultima_carpeta = Path(DATA_DIR)

        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 820)
        self.setMinimumSize(900, 650)

        self._construir_acciones()
        self._construir_ui()
        self._construir_menu()
        self._construir_barra_estado()
        self._cargar_datos_iniciales()

    def _construir_acciones(self) -> None:
        self.accion_importar = QAction("&Importar rutinas CSV...", self)
        self.accion_importar.setShortcut("Ctrl+O")
        self.accion_importar.setStatusTip("Cargar un archivo CSV de rutinas")
        self.accion_importar.triggered.connect(self._importar_rutinas)

        self.accion_salir = QAction("&Salir", self)
        self.accion_salir.setShortcut("Ctrl+Q")
        self.accion_salir.triggered.connect(self.close)

        self.accion_acerca = QAction("&Acerca de FitPlan", self)
        self.accion_acerca.triggered.connect(self._acerca_de)

    def _construir_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.rutinas_tab = RutinasTab(self.rutina_service)
        self.rutinas_tab.importar_solicitado.connect(self._importar_rutinas)
        self.tabs.addTab(self.rutinas_tab, "Rutinas")

        self.setCentralWidget(self.tabs)

    def _construir_menu(self) -> None:
        menu_archivo = self.menuBar().addMenu("&Archivo")
        menu_archivo.addAction(self.accion_importar)
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.accion_salir)

        menu_ayuda = self.menuBar().addMenu("A&yuda")
        menu_ayuda.addAction(self.accion_acerca)

    def _construir_barra_estado(self) -> None:
        self.etiqueta_estado = QLabel("Sin rutinas cargadas")
        self.statusBar().addPermanentWidget(self.etiqueta_estado)

    def _cargar_datos_iniciales(self) -> None:
        try:
            total = self.rutina_service.cargar()
        except FitPlanError as exc:
            self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)
            self.etiqueta_estado.setText("Sin rutinas cargadas")
            self._mostrar_error("No se pudieron cargar las rutinas", exc)
            return

        self._ultima_carpeta = self.rutina_service.ruta.parent
        self._aplicar_rutinas(
            total,
            self.rutina_service.ruta.name,
            "Datos iniciales cargados",
        )

    def _importar_rutinas(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar rutinas",
            str(self._ultima_carpeta),
            "Archivos CSV (*.csv);;Todos los archivos (*)",
        )
        if not ruta:
            return

        try:
            total = self.rutina_service.cargar(ruta)
        except FitPlanError as exc:
            self._mostrar_error("No se pudo importar el archivo", exc)
            return

        self._ultima_carpeta = Path(ruta).parent
        self._aplicar_rutinas(
            total,
            Path(ruta).name,
            "Archivo importado correctamente",
        )

    def _aplicar_rutinas(self, total: int, nombre_archivo: str, mensaje: str) -> None:
        self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)
        self.etiqueta_estado.setText(f"{total} rutinas · {nombre_archivo}")
        self.statusBar().showMessage(mensaje, 4000)

    def _mostrar_error(self, titulo: str, error: Exception) -> None:
        QMessageBox.critical(self, titulo, str(error))

    def _acerca_de(self) -> None:
        QMessageBox.about(
            self,
            "Acerca de FitPlan",
            (
                f"<h3>FitPlan {APP_VERSION}</h3>"
                "<p>Gestor de rutinas de entrenamiento y planificación nutricional.</p>"
                "<p>Desarrollado en Python con PyQt5.</p>"
            ),
        )
