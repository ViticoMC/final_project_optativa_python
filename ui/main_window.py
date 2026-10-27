from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QLabel,
    QMainWindow,
    QTabWidget,
)

from app.config import APP_TITLE, DATA_DIR
from app.exceptions import FitPlanError
from services.container import AppServices
from ui.dialogs import mostrar_acerca_de, mostrar_error
from ui.widgets.ejercicios_tab import EjerciciosTab
from ui.widgets.estadisticas_tab import EstadisticasTab
from ui.widgets.mi_plan_tab import MiPlanTab
from ui.widgets.nutricion_tab import NutricionTab
from ui.widgets.rutinas_tab import RutinasTab


class MainWindow(QMainWindow):
    def __init__(
        self,
        servicios: AppServices,
        settings: QSettings | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self._settings = settings
        self.rutina_service = servicios.rutinas
        self.ejercicio_service = servicios.ejercicios
        self.nutricion_service = servicios.nutricion
        self.estadistica_service = servicios.estadisticas
        self.exportacion_service = servicios.exportacion
        self.plantilla_service = servicios.plantillas
        self.comida_personal_service = servicios.comidas_personales
        self._ultima_carpeta = self._carpeta_preferida(
            "rutas/importacion",
            Path(DATA_DIR),
        )
        self._carpeta_exportacion = self._carpeta_preferida(
            "rutas/exportacion",
            Path.home(),
        )

        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 820)
        self.setMinimumSize(900, 650)

        self._construir_acciones()
        self._construir_ui()
        self._construir_menu()
        self._construir_barra_estado()
        self._restaurar_ventana()
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

        self.accion_exportar_plantillas = QAction(
            "Exportar mis &rutinas...",
            self,
        )
        self.accion_exportar_plantillas.setStatusTip(
            "Guardar en CSV la biblioteca de plantillas personales"
        )
        self.accion_exportar_plantillas.triggered.connect(
            self._exportar_plantillas
        )

        self.accion_exportar_comidas_personales = QAction(
            "Exportar mis &comidas...",
            self,
        )
        self.accion_exportar_comidas_personales.setStatusTip(
            "Guardar en CSV las comidas personales"
        )
        self.accion_exportar_comidas_personales.triggered.connect(
            self._exportar_comidas_personales
        )

        self.accion_recargar = QAction("&Recargar datos", self)
        self.accion_recargar.setShortcut("F5")
        self.accion_recargar.setStatusTip(
            "Volver a leer los datos estándar y personales"
        )
        self.accion_recargar.triggered.connect(self._recargar_datos)

        self.accion_ver_rutinas = self._crear_accion_pestana(
            "&Rutinas",
            "Ctrl+1",
            0,
        )
        self.accion_ver_ejercicios = self._crear_accion_pestana(
            "&Ejercicios",
            "Ctrl+2",
            1,
        )
        self.accion_ver_nutricion = self._crear_accion_pestana(
            "&Nutrición",
            "Ctrl+3",
            2,
        )
        self.accion_ver_estadisticas = self._crear_accion_pestana(
            "&Estadísticas",
            "Ctrl+4",
            3,
        )
        self.accion_ver_mi_plan = self._crear_accion_pestana(
            "Mi &plan",
            "Ctrl+5",
            4,
        )

        self.accion_salir = QAction("&Salir", self)
        self.accion_salir.setShortcut("Ctrl+Q")
        self.accion_salir.triggered.connect(self.close)

        self.accion_acerca = QAction("&Acerca de FitPlan", self)
        self.accion_acerca.triggered.connect(self._acerca_de)

    def _crear_accion_pestana(
        self,
        texto: str,
        atajo: str,
        indice: int,
    ) -> QAction:
        accion = QAction(texto, self)
        accion.setShortcut(atajo)
        accion.setStatusTip(
            f"Ir a la pestaña {texto.replace('&', '')}"
        )
        accion.triggered.connect(
            lambda: self.tabs.setCurrentIndex(indice)
        )
        return accion

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

        self.mi_plan_tab = MiPlanTab(
            self.plantilla_service,
            self.comida_personal_service,
        )
        self.mi_plan_tab.exportar_plantillas_solicitado.connect(
            self._exportar_plantillas
        )
        self.mi_plan_tab.exportar_comidas_solicitado.connect(
            self._exportar_comidas_personales
        )
        self.mi_plan_tab.datos_cambiados.connect(
            self._actualizar_estado_global
        )
        self.tabs.addTab(self.mi_plan_tab, "Mi plan")

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
        menu_exportar.addSeparator()
        menu_exportar.addAction(self.accion_exportar_plantillas)
        menu_exportar.addAction(self.accion_exportar_comidas_personales)

        menu_archivo.addSeparator()
        menu_archivo.addAction(self.accion_salir)

        menu_ver = self.menuBar().addMenu("&Ver")
        menu_ver.addAction(self.accion_ver_rutinas)
        menu_ver.addAction(self.accion_ver_ejercicios)
        menu_ver.addAction(self.accion_ver_nutricion)
        menu_ver.addAction(self.accion_ver_estadisticas)
        menu_ver.addAction(self.accion_ver_mi_plan)
        menu_ver.addSeparator()
        menu_ver.addAction(self.accion_recargar)

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

        try:
            self.plantilla_service.cargar()
        except FitPlanError as exc:
            self._mostrar_error("No se pudieron cargar mis rutinas", exc)

        try:
            self.comida_personal_service.cargar()
        except FitPlanError as exc:
            self._mostrar_error("No se pudieron cargar mis comidas", exc)

        self.mi_plan_tab.refrescar_datos()
        self._actualizar_estado_global()
        self.estadisticas_tab.refrescar_datos()
        if (
            self.rutina_service.total()
            or self.ejercicio_service.total()
            or self.nutricion_service.total()
            or self.plantilla_service.total()
            or self.comida_personal_service.total()
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

    def _recargar_datos(self) -> None:
        fuentes = (
            ("rutinas", self.rutina_service),
            ("catálogo", self.ejercicio_service),
            ("plan nutricional", self.nutricion_service),
            ("mis plantillas", self.plantilla_service),
            ("mis comidas", self.comida_personal_service),
        )
        fallos: list[str] = []

        for nombre, servicio in fuentes:
            try:
                servicio.cargar()
            except FitPlanError as exc:
                fallos.append(f"{nombre}: {exc}")

        self.rutinas_tab.refrescar_datos()
        self.ejercicios_tab.refrescar_datos()
        self.nutricion_tab.refrescar_datos()
        self.estadisticas_tab.refrescar_datos()
        self.mi_plan_tab.refrescar_datos()
        self._actualizar_estado_global()

        if fallos:
            self.statusBar().showMessage(
                "Recarga completada con incidencias",
                5000,
            )
            self._mostrar_error(
                "No se pudieron recargar todos los datos",
                FitPlanError("\n".join(fallos)),
            )
        else:
            self.statusBar().showMessage(
                "Datos recargados correctamente",
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

    def _exportar_plantillas(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar mis rutinas",
            "mis_rutinas_exportadas.csv",
        )
        if ruta is None:
            return

        registros = self.mi_plan_tab.plantillas_visibles()
        try:
            destino = self.exportacion_service.exportar_plantillas(
                ruta,
                registros,
            )
        except FitPlanError as exc:
            self._mostrar_error(
                "No se pudieron exportar mis rutinas",
                exc,
            )
            return

        self._finalizar_exportacion("plantillas", len(registros), destino)

    def _exportar_comidas_personales(self) -> None:
        ruta = self._solicitar_ruta_exportacion(
            "Exportar mis comidas",
            "mis_comidas_exportadas.csv",
        )
        if ruta is None:
            return

        registros = self.mi_plan_tab.comidas_visibles()
        try:
            destino = self.exportacion_service.exportar_comidas_personales(
                ruta,
                registros,
            )
        except FitPlanError as exc:
            self._mostrar_error(
                "No se pudieron exportar mis comidas",
                exc,
            )
            return

        self._finalizar_exportacion(
            "comidas personales",
            len(registros),
            destino,
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
            f"{self.nutricion_service.total()} comidas · "
            f"{self.plantilla_service.total()} plantillas · "
            f"{self.comida_personal_service.total()} mis comidas"
        )

    def _mostrar_error(self, titulo: str, error: Exception) -> None:
        mostrar_error(self, titulo, error)

    def _acerca_de(self) -> None:
        mostrar_acerca_de(self)

    def _carpeta_preferida(
        self,
        clave: str,
        predeterminada: Path,
    ) -> Path:
        if self._settings is None:
            return predeterminada

        valor = self._settings.value(clave, "")
        if valor:
            ruta = Path(str(valor))
            if ruta.is_dir():
                return ruta
        return predeterminada

    def _restaurar_ventana(self) -> None:
        if self._settings is None:
            return

        geometria = self._settings.value("ventana/geometria")
        if geometria is not None:
            self.restoreGeometry(geometria)

        try:
            indice = int(self._settings.value("ventana/pestana", 0))
        except (TypeError, ValueError):
            indice = 0
        if 0 <= indice < self.tabs.count():
            self.tabs.setCurrentIndex(indice)

    def _guardar_preferencias(self) -> None:
        if self._settings is None:
            return

        self._settings.setValue("ventana/geometria", self.saveGeometry())
        self._settings.setValue(
            "ventana/pestana",
            self.tabs.currentIndex(),
        )
        self._settings.setValue(
            "rutas/importacion",
            str(self._ultima_carpeta),
        )
        self._settings.setValue(
            "rutas/exportacion",
            str(self._carpeta_exportacion),
        )
        self._settings.sync()

    def closeEvent(self, event) -> None:
        self._guardar_preferencias()
        super().closeEvent(event)
