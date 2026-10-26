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
from services.container import AppServices
from ui.widgets.ejercicios_tab import EjerciciosTab
from ui.widgets.rutinas_tab import RutinasTab


class MainWindow(QMainWindow):
    def __init__(
        self,
        servicios: AppServices,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self.rutina_service = servicios.rutinas
        self.ejercicio_service = servicios.ejercicios
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

        self.accion_importar_ejercicios = QAction(
            "Importar &catálogo CSV...", self
        )
        self.accion_importar_ejercicios.setShortcut("Ctrl+Shift+O")
        self.accion_importar_ejercicios.setStatusTip(
            "Cargar un archivo CSV de ejercicios"
        )
        self.accion_importar_ejercicios.triggered.connect(
            self._importar_ejercicios
        )

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

        self.ejercicios_tab = EjerciciosTab(
            self.ejercicio_service,
            self.rutina_service,
        )
        self.ejercicios_tab.importar_solicitado.connect(
            self._importar_ejercicios
        )
        self.tabs.addTab(self.ejercicios_tab, "Ejercicios")

        self.setCentralWidget(self.tabs)

    def _construir_menu(self) -> None:
        menu_archivo = self.menuBar().addMenu("&Archivo")
        menu_archivo.addAction(self.accion_importar)
        menu_archivo.addAction(self.accion_importar_ejercicios)
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.accion_salir)

        menu_ayuda = self.menuBar().addMenu("A&yuda")
        menu_ayuda.addAction(self.accion_acerca)

    def _construir_barra_estado(self) -> None:
        self.etiqueta_estado = QLabel("Sin datos cargados")
        self.statusBar().addPermanentWidget(self.etiqueta_estado)

    def _cargar_datos_iniciales(self) -> None:
        try:
            self.rutina_service.cargar()
        except FitPlanError as exc:
            self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)
            self._mostrar_error("No se pudieron cargar las rutinas", exc)
        else:
            self._ultima_carpeta = self.rutina_service.ruta.parent
            self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)

        try:
            self.ejercicio_service.cargar()
        except FitPlanError as exc:
            self.ejercicios_tab.refrescar_datos(reiniciar_filtros=True)
            self._mostrar_error("No se pudo cargar el catálogo", exc)
        else:
            self.ejercicios_tab.refrescar_datos(reiniciar_filtros=True)

        self._actualizar_estado_global()
        if self.rutina_service.total() or self.ejercicio_service.total():
            self.statusBar().showMessage("Datos iniciales cargados", 4000)

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

    def _importar_ejercicios(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar catálogo de ejercicios",
            str(self._ultima_carpeta),
            "Archivos CSV (*.csv);;Todos los archivos (*)",
        )
        if not ruta:
            return

        try:
            total = self.ejercicio_service.cargar(ruta)
        except FitPlanError as exc:
            self._mostrar_error("No se pudo importar el catálogo", exc)
            return

        self._ultima_carpeta = Path(ruta).parent
        self.ejercicios_tab.refrescar_datos(reiniciar_filtros=True)
        self._actualizar_estado_global()
        self.statusBar().showMessage(
            f"Catálogo importado: {total} ejercicios · {Path(ruta).name}",
            4000,
        )

    def _aplicar_rutinas(
        self,
        total: int,
        nombre_archivo: str,
        mensaje: str,
    ) -> None:
        self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)
        self.ejercicios_tab.actualizar_cobertura()
        self._actualizar_estado_global()
        self.statusBar().showMessage(
            f"{mensaje}: {total} rutinas · {nombre_archivo}",
            4000,
        )

    def _actualizar_estado_global(self) -> None:
        self.etiqueta_estado.setText(
            f"{self.rutina_service.total()} rutinas · "
            f"{self.ejercicio_service.total()} ejercicios"
        )

    def _mostrar_error(self, titulo: str, error: Exception) -> None:
        QMessageBox.critical(self, titulo, str(error))

    def _acerca_de(self) -> None:
        QMessageBox.about(
            self,
            "Acerca de FitPlan",
            (
                f"<h3>FitPlan {APP_VERSION}</h3>"
                "<p>Gestor de rutinas de entrenamiento, catálogo de ejercicios "
                "y planificación nutricional.</p>"
                "<p>Desarrollado en Python con PyQt5.</p>"
            ),
        )
