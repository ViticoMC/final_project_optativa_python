from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.exceptions import FitPlanError
from app.models import Comida, PlantillaRutina
from app.utils import normalizar_texto
from services.comida_personal_service import ComidaPersonalService
from services.plantilla_service import PlantillaService
from ui.dialogs import mostrar_error
from ui.dialogs_personal import (
    DialogoComidaPersonal,
    DialogoPlantillaRutina,
)
from ui.models.table_models import (
    ComidaTableModel,
    PlantillaRutinaTableModel,
)


class PlantillasPanel(QWidget):
    exportar_solicitado = pyqtSignal()
    datos_cambiados = pyqtSignal()

    def __init__(
        self,
        servicio: PlantillaService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.modelo = PlantillaRutinaTableModel()
        self._construir_ui()
        self.refrescar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)

        titulo = QLabel("Mis rutinas")
        fuente = titulo.font()
        fuente.setPointSize(13)
        fuente.setBold(True)
        titulo.setFont(fuente)

        subtitulo = QLabel(
            "Biblioteca de plantillas creadas con ejercicios del catálogo."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecera.addLayout(textos)
        cabecera.addStretch(1)

        self.boton_exportar = QPushButton("Exportar mis rutinas CSV")
        self.boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        self.boton_editar = QPushButton("Editar")
        self.boton_editar.clicked.connect(self.editar)
        self.boton_eliminar = QPushButton("Eliminar")
        self.boton_eliminar.clicked.connect(self.eliminar)
        self.boton_nueva = QPushButton("Nueva plantilla")
        self.boton_nueva.setObjectName("boton_primario")
        self.boton_nueva.clicked.connect(self.crear)

        cabecera.addWidget(self.boton_exportar)
        cabecera.addWidget(self.boton_editar)
        cabecera.addWidget(self.boton_eliminar)
        cabecera.addWidget(self.boton_nueva)
        layout.addLayout(cabecera)

        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSortingEnabled(True)
        self.tabla.sortByColumn(0, Qt.AscendingOrder)
        self.tabla.setWordWrap(False)
        self.tabla.verticalHeader().setVisible(False)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setMinimumSectionSize(70)
        encabezado.setSectionResizeMode(QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(2, QHeaderView.Stretch)
        encabezado.setStretchLastSection(False)
        self.tabla.selectionModel().currentRowChanged.connect(
            self._actualizar_botones
        )
        self.tabla.doubleClicked.connect(self.editar)
        layout.addWidget(self.tabla, 1)

        self.etiqueta_estado = QLabel()
        self.etiqueta_estado.setObjectName("estado_tabla")
        layout.addWidget(self.etiqueta_estado)

    def refrescar_datos(self) -> None:
        cabecera = self.tabla.horizontalHeader()
        columna = cabecera.sortIndicatorSection()
        orden = cabecera.sortIndicatorOrder()

        self.modelo.set_registros(self.servicio.todas())
        if self.tabla.isSortingEnabled() and columna >= 0:
            self.modelo.sort(columna, orden)
        self._actualizar_estado()
        self._actualizar_botones()

    def registro_actual(self) -> PlantillaRutina | None:
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return None
        registro = self.modelo.registro_en(filas[0].row())
        return registro if isinstance(registro, PlantillaRutina) else None

    def plantillas_visibles(self) -> tuple[PlantillaRutina, ...]:
        return tuple(
            registro
            for registro in self.modelo.registros()
            if isinstance(registro, PlantillaRutina)
        )

    def crear(self) -> None:
        dialogo = DialogoPlantillaRutina(self.servicio, parent=self)
        if dialogo.exec_() == dialogo.Accepted:
            self.refrescar_datos()
            self.datos_cambiados.emit()

    def editar(self, *_args: object) -> None:
        plantilla = self.registro_actual()
        if plantilla is None:
            return
        dialogo = DialogoPlantillaRutina(
            self.servicio,
            plantilla=plantilla,
            parent=self,
        )
        if dialogo.exec_() == dialogo.Accepted:
            self.refrescar_datos()
            self.datos_cambiados.emit()

    def eliminar(self) -> None:
        plantilla = self.registro_actual()
        if plantilla is None:
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar plantilla",
            (
                f"¿Eliminar la plantilla {plantilla.id_plantilla}? "
                "Esta acción no modifica los datos estándar."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.servicio.eliminar(plantilla.id_plantilla)
        except FitPlanError as exc:
            mostrar_error(self, "No se pudo eliminar la plantilla", exc)
            return
        self.refrescar_datos()
        self.datos_cambiados.emit()

    def _actualizar_botones(self, *_args: object) -> None:
        hay_seleccion = self.registro_actual() is not None
        self.boton_editar.setEnabled(hay_seleccion)
        self.boton_eliminar.setEnabled(hay_seleccion)

    def _actualizar_estado(self) -> None:
        total = self.servicio.total()
        if total == 0:
            self.etiqueta_estado.setText(
                "Aún no hay plantillas. Crea una con ejercicios del catálogo."
            )
            return
        ejercicios = {
            normalizar_texto(ejercicio)
            for plantilla in self.servicio.todas()
            for ejercicio in plantilla.ejercicios
        }
        self.etiqueta_estado.setText(
            f"{total} plantilla(s) · {len(ejercicios)} ejercicio(s) distinto(s)."
        )


class ComidasPersonalesPanel(QWidget):
    exportar_solicitado = pyqtSignal()
    datos_cambiados = pyqtSignal()

    def __init__(
        self,
        servicio: ComidaPersonalService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.modelo = ComidaTableModel()
        self._construir_ui()
        self.refrescar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)

        titulo = QLabel("Mis comidas")
        fuente = titulo.font()
        fuente.setPointSize(13)
        fuente.setBold(True)
        titulo.setFont(fuente)

        subtitulo = QLabel(
            "Combinaciones propias creadas con alimentos del plan estándar."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecera.addLayout(textos)
        cabecera.addStretch(1)

        self.boton_exportar = QPushButton("Exportar mis comidas CSV")
        self.boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        self.boton_editar = QPushButton("Editar")
        self.boton_editar.clicked.connect(self.editar)
        self.boton_eliminar = QPushButton("Eliminar")
        self.boton_eliminar.clicked.connect(self.eliminar)
        self.boton_nueva = QPushButton("Nueva comida")
        self.boton_nueva.setObjectName("boton_primario")
        self.boton_nueva.clicked.connect(self.crear)

        cabecera.addWidget(self.boton_exportar)
        cabecera.addWidget(self.boton_editar)
        cabecera.addWidget(self.boton_eliminar)
        cabecera.addWidget(self.boton_nueva)
        layout.addLayout(cabecera)

        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSortingEnabled(True)
        self.tabla.sortByColumn(0, Qt.AscendingOrder)
        self.tabla.setWordWrap(False)
        self.tabla.verticalHeader().setVisible(False)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setMinimumSectionSize(70)
        encabezado.setSectionResizeMode(QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(3, QHeaderView.Stretch)
        encabezado.setSectionResizeMode(5, QHeaderView.Stretch)
        encabezado.setStretchLastSection(False)
        self.tabla.selectionModel().currentRowChanged.connect(
            self._actualizar_botones
        )
        self.tabla.doubleClicked.connect(self.editar)
        layout.addWidget(self.tabla, 1)

        self.etiqueta_estado = QLabel()
        self.etiqueta_estado.setObjectName("estado_tabla")
        layout.addWidget(self.etiqueta_estado)

    def refrescar_datos(self) -> None:
        cabecera = self.tabla.horizontalHeader()
        columna = cabecera.sortIndicatorSection()
        orden = cabecera.sortIndicatorOrder()

        self.modelo.set_registros(self.servicio.todas())
        if self.tabla.isSortingEnabled() and columna >= 0:
            self.modelo.sort(columna, orden)
        self._actualizar_estado()
        self._actualizar_botones()

    def registro_actual(self) -> Comida | None:
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return None
        registro = self.modelo.registro_en(filas[0].row())
        return registro if isinstance(registro, Comida) else None

    def comidas_visibles(self) -> tuple[Comida, ...]:
        return tuple(
            registro
            for registro in self.modelo.registros()
            if isinstance(registro, Comida)
        )

    def crear(self) -> None:
        dialogo = DialogoComidaPersonal(self.servicio, parent=self)
        if dialogo.exec_() == dialogo.Accepted:
            self.refrescar_datos()
            self.datos_cambiados.emit()

    def editar(self, *_args: object) -> None:
        comida = self.registro_actual()
        if comida is None:
            return
        dialogo = DialogoComidaPersonal(
            self.servicio,
            comida=comida,
            parent=self,
        )
        if dialogo.exec_() == dialogo.Accepted:
            self.refrescar_datos()
            self.datos_cambiados.emit()

    def eliminar(self) -> None:
        comida = self.registro_actual()
        if comida is None:
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar comida",
            (
                f"¿Eliminar la comida {comida.id_plan}? "
                "Esta acción no modifica los datos estándar."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.servicio.eliminar(comida.id_plan)
        except FitPlanError as exc:
            mostrar_error(self, "No se pudo eliminar la comida", exc)
            return
        self.refrescar_datos()
        self.datos_cambiados.emit()

    def _actualizar_botones(self, *_args: object) -> None:
        hay_seleccion = self.registro_actual() is not None
        self.boton_editar.setEnabled(hay_seleccion)
        self.boton_eliminar.setEnabled(hay_seleccion)

    def _actualizar_estado(self) -> None:
        total = self.servicio.total()
        if total == 0:
            self.etiqueta_estado.setText(
                "Aún no hay comidas propias. Crea una con alimentos estándar."
            )
            return
        alimentos = {
            normalizar_texto(alimento)
            for comida in self.servicio.todas()
            for alimento in comida.alimentos
        }
        self.etiqueta_estado.setText(
            f"{total} comida(s) · {len(alimentos)} alimento(s) distinto(s)."
        )


class MiPlanTab(QWidget):
    exportar_plantillas_solicitado = pyqtSignal()
    exportar_comidas_solicitado = pyqtSignal()
    datos_cambiados = pyqtSignal()

    def __init__(
        self,
        plantillas: PlantillaService,
        comidas: ComidaPersonalService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._construir_ui(plantillas, comidas)

    def _construir_ui(
        self,
        plantillas: PlantillaService,
        comidas: ComidaPersonalService,
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        titulo = QLabel("Mi plan personal")
        fuente = titulo.font()
        fuente.setPointSize(16)
        fuente.setBold(True)
        titulo.setFont(fuente)

        subtitulo = QLabel(
            "Tus plantillas y comidas se construyen solo con opciones de los "
            "CSV estándar. Los archivos estándar no se modifican."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        self.subtabs = QTabWidget()
        self.subtabs.setDocumentMode(True)

        self.plantillas_panel = PlantillasPanel(plantillas)
        self.plantillas_panel.exportar_solicitado.connect(
            self.exportar_plantillas_solicitado.emit
        )
        self.plantillas_panel.datos_cambiados.connect(
            self.datos_cambiados.emit
        )
        self.subtabs.addTab(self.plantillas_panel, "Mis rutinas")

        self.comidas_panel = ComidasPersonalesPanel(comidas)
        self.comidas_panel.exportar_solicitado.connect(
            self.exportar_comidas_solicitado.emit
        )
        self.comidas_panel.datos_cambiados.connect(self.datos_cambiados.emit)
        self.subtabs.addTab(self.comidas_panel, "Mis comidas")

        layout.addWidget(self.subtabs, 1)

    @property
    def tabla_plantillas(self) -> QTableView:
        return self.plantillas_panel.tabla

    @property
    def tabla_comidas(self) -> QTableView:
        return self.comidas_panel.tabla

    def plantillas_visibles(self) -> tuple[PlantillaRutina, ...]:
        return self.plantillas_panel.plantillas_visibles()

    def comidas_visibles(self) -> tuple[Comida, ...]:
        return self.comidas_panel.comidas_visibles()

    def refrescar_datos(self) -> None:
        self.plantillas_panel.refrescar_datos()
        self.comidas_panel.refrescar_datos()
