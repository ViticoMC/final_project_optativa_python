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
from ui.widgets.estadisticas_tab import EstadisticasTab
from ui.widgets.nutricion_tab import NutricionTab
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
        self.nutricion_service = servicios.nutricion
        self.estadistica_service = servicios.estadisticas
        self.exportacion_service = servicios.exportacion
        self._ultima_carpeta = Path(DATA_DIR)
        self._carpeta_exportacion = Path.home()

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

        self.accion_importar_nutricion = QAction(
            "Importar plan &nutricional CSV...", self
        )
        self.accion_importar_nutricion.setShortcut("Ctrl+Shift+N")
        self.accion_importar_nutricion.setStatusTip(
            "Cargar un archivo CSV con el plan de alimentación"
        )
        self.accion_importar_nutricion.triggered.connect(
            self._importar_nutricion
        )

        self.accion_exportar_rutinas = QAction(
            "Exportar &rutinas visibles...",
            self,
        )
        self.accion_exportar_rutinas.setStatusTip(
            "Guardar en CSV las rutinas que coinciden con los filtros"
        )
        self.accion_exportar_rutinas.triggered.connect(self._exportar_rutinas)

        self.accion_exportar_ejercicios = QAction(
            "Exportar &catálogo visible...",
            self,
        )
        self.accion_exportar_ejercicios.setStatusTip(
            "Guardar en CSV los ejercicios que coinciden con los filtros"
        )
        self.accion_exportar_ejercicios.triggered.connect(
            self._exportar_ejercicios
        )

        self.accion_exportar_nutricion = QAction(
            "Exportar &plan visible...",
            self,
        )
        self.accion_exportar_nutricion.setStatusTip(
            "Guardar en CSV las comidas que coinciden con los filtros"
        )
        self.accion_exportar_nutricion.triggered.connect(
            self._exportar_nutricion
        )

        self.accion_exportar_estadisticas = QAction(
            "Exportar &estadísticas...",
            self,
        )
        self.accion_exportar_estadisticas.setStatusTip(
            "Guardar un resumen de indicadores y distribuciones en CSV"
        )
        self.accion_exportar_estadisticas.triggered.connect(
            self._exportar_estadisticas
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
        self.rutinas_tab.exportar_solicitado.connect(self._exportar_rutinas)
        self.tabs.addTab(self.rutinas_tab, "Rutinas")

        self.ejercicios_tab = EjerciciosTab(
            self.ejercicio_service,
            self.rutina_service,
        )
        self.ejercicios_tab.importar_solicitado.connect(
            self._importar_ejercicios
        )
        self.ejercicios_tab.exportar_solicitado.connect(
            self._exportar_ejercicios
        )
        self.tabs.addTab(self.ejercicios_tab, "Ejercicios")

        self.nutricion_tab = NutricionTab(self.nutricion_service)
        self.nutricion_tab.importar_solicitado.connect(
            self._importar_nutricion
        )
        self.nutricion_tab.exportar_solicitado.connect(
            self._exportar_nutricion
        )
        self.tabs.addTab(self.nutricion_tab, "Nutrición")

        self.estadisticas_tab = EstadisticasTab(
            self.estadistica_service,
            self.rutina_service,
            self.ejercicio_service,
            self.nutricion_service,
        )
        self.estadisticas_tab.exportar_solicitado.connect(
            self._exportar_estadisticas
        )
        self.tabs.addTab(self.estadisticas_tab, "Estadísticas")

        self.setCentralWidget(self.tabs)

    def _construir_menu(self) -> None:
        menu_archivo = self.menuBar().addMenu("&Archivo")
        menu_archivo.addAction(self.accion_importar)
        menu_archivo.addAction(self.accion_importar_ejercicios)
        menu_archivo.addAction(self.accion_importar_nutricion)
        menu_archivo.addSeparator()

        menu_exportar = menu_archivo.addMenu("&Exportar")
        menu_exportar.addAction(self.accion_exportar_rutinas)
        menu_exportar.addAction(self.accion_exportar_ejercicios)
        menu_exportar.addAction(self.accion_exportar_nutricion)
        menu_exportar.addSeparator()
        menu_exportar.addAction(self.accion_exportar_estadisticas)

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

        try:
            self.nutricion_service.cargar()
        except FitPlanError as exc:
            self.nutricion_tab.refrescar_datos(reiniciar_filtros=True)
            self._mostrar_error("No se pudo cargar el plan nutricional", exc)
        else:
            self.nutricion_tab.refrescar_datos(reiniciar_filtros=True)

        self._actualizar_estado_global()
        self.estadisticas_tab.refrescar_datos()
        if (
            self.rutina_service.total()
            or self.ejercicio_service.total()
            or self.nutricion_service.total()
        ):
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
        self.estadisticas_tab.refrescar_datos()
        self._actualizar_estado_global()
        self.statusBar().showMessage(
            f"Catálogo importado: {total} ejercicios · {Path(ruta).name}",
            4000,
        )

    def _importar_nutricion(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar plan de alimentación",
            str(self._ultima_carpeta),
            "Archivos CSV (*.csv);;Todos los archivos (*)",
        )
        if not ruta:
            return

        try:
            total = self.nutricion_service.cargar(ruta)
        except FitPlanError as exc:
            self._mostrar_error("No se pudo importar el plan nutricional", exc)
            return

        self._ultima_carpeta = Path(ruta).parent
        self.nutricion_tab.refrescar_datos(reiniciar_filtros=True)
        self.estadisticas_tab.refrescar_datos()
        self._actualizar_estado_global()
        self.statusBar().showMessage(
            f"Plan nutricional importado: {total} comidas · {Path(ruta).name}",
            4000,
        )

    def _exportar_rutinas(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar rutinas visibles",
            "rutinas_exportadas.csv",
        )
        if ruta is None:
            return

        registros = self.rutinas_tab.registros_visibles()
        try:
            destino = self.exportacion_service.exportar_rutinas(
                ruta,
                registros,
            )
        except FitPlanError as exc:
            self._mostrar_error("No se pudieron exportar las rutinas", exc)
            return

        self._finalizar_exportacion("rutinas", len(registros), destino)

    def _exportar_ejercicios(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar catálogo visible",
            "catalogo_exportado.csv",
        )
        if ruta is None:
            return

        registros = self.ejercicios_tab.registros_visibles()
        try:
            destino = self.exportacion_service.exportar_ejercicios(
                ruta,
                registros,
            )
        except FitPlanError as exc:
            self._mostrar_error("No se pudo exportar el catálogo", exc)
            return

        self._finalizar_exportacion("ejercicios", len(registros), destino)

    def _exportar_nutricion(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar plan visible",
            "plan_alimentacion_exportado.csv",
        )
        if ruta is None:
            return

        registros = self.nutricion_tab.registros_visibles()
        try:
            destino = self.exportacion_service.exportar_comidas(
                ruta,
                registros,
            )
        except FitPlanError as exc:
            self._mostrar_error("No se pudo exportar el plan", exc)
            return

        self._finalizar_exportacion("comidas", len(registros), destino)

    def _exportar_estadisticas(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar estadísticas",
            "estadisticas_fitplan.csv",
        )
        if ruta is None:
            return

        estadisticas = self.estadistica_service.calcular(
            self.rutina_service.todas(),
            self.ejercicio_service.todos(),
            self.nutricion_service.todos(),
        )
        try:
            destino = self.exportacion_service.exportar_estadisticas(
                ruta,
                estadisticas,
            )
        except FitPlanError as exc:
            self._mostrar_error(
                "No se pudieron exportar las estadísticas",
                exc,
            )
            return

        self._carpeta_exportacion = destino.parent
        self.statusBar().showMessage(
            f"Estadísticas exportadas · {destino.name}",
            5000,
        )

    def _solicitar_ruta_exportacion(
        self,
        titulo: str,
        nombre_sugerido: str,
    ) -> Path | None:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            titulo,
            str(self._carpeta_exportacion / nombre_sugerido),
            "Archivos CSV (*.csv)",
        )
        return Path(ruta) if ruta else None

    def _finalizar_exportacion(
        self,
        etiqueta: str,
        cantidad: int,
        destino: Path,
    ) -> None:
        self._carpeta_exportacion = destino.parent
        self.statusBar().showMessage(
            f"Exportación completada: {cantidad} {etiqueta} · {destino.name}",
            5000,
        )

    def _aplicar_rutinas(
        self,
        total: int,
        nombre_archivo: str,
        mensaje: str,
    ) -> None:
        self.rutinas_tab.refrescar_datos(reiniciar_filtros=True)
        self.ejercicios_tab.actualizar_cobertura()
        self.estadisticas_tab.refrescar_datos()
        self._actualizar_estado_global()
        self.statusBar().showMessage(
            f"{mensaje}: {total} rutinas · {nombre_archivo}",
            4000,
        )

    def _actualizar_estado_global(self) -> None:
        self.etiqueta_estado.setText(
            f"{self.rutina_service.total()} rutinas · "
            f"{self.ejercicio_service.total()} ejercicios · "
            f"{self.nutricion_service.total()} comidas"
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
