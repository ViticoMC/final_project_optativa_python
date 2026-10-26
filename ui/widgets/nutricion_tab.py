from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QShortcut,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.models import Comida
from services.nutricion_service import NutricionService
from ui.models.table_models import ComidaTableModel


class NutricionTab(QWidget):
    importar_solicitado = pyqtSignal()

    def __init__(self, nutricion_service: NutricionService, parent=None) -> None:
        super().__init__(parent)
        self.nutricion_service = nutricion_service
        self.modelo = ComidaTableModel()
        self._construir_ui()
        self.refrescar_datos(reiniciar_filtros=True)

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addLayout(self._construir_cabecera())
        layout.addLayout(self._construir_filtros())
        layout.addWidget(self._construir_contenido(), 1)

        self.etiqueta_estado = QLabel()
        self.etiqueta_estado.setObjectName("estado_tabla")
        layout.addWidget(self.etiqueta_estado)

    def _construir_cabecera(self) -> QHBoxLayout:
        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)

        titulo = QLabel("Plan de alimentación")
        fuente_titulo = titulo.font()
        fuente_titulo.setPointSize(16)
        fuente_titulo.setBold(True)
        titulo.setFont(fuente_titulo)

        subtitulo = QLabel(
            "Consulta las comidas del día, los alimentos sugeridos y las "
            "observaciones para adaptar el plan a tus objetivos."
        )
        subtitulo.setObjectName("subtitulo")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        derecha = QVBoxLayout()
        derecha.setSpacing(4)

        self.boton_importar = QPushButton("Importar plan CSV")
        self.boton_importar.setToolTip(
            "Seleccionar un archivo CSV con el plan de alimentación"
        )
        self.boton_importar.clicked.connect(self.importar_solicitado.emit)

        self.etiqueta_resumen = QLabel()
        self.etiqueta_resumen.setWordWrap(True)
        self.etiqueta_resumen.setAlignment(Qt.AlignRight)
        self.etiqueta_resumen.setTextFormat(Qt.PlainText)

        derecha.addWidget(self.boton_importar, 0, Qt.AlignRight)
        derecha.addWidget(self.etiqueta_resumen)

        cabecera.addLayout(textos)
        cabecera.addStretch(1)
        cabecera.addLayout(derecha)
        return cabecera

    def _construir_filtros(self) -> QGridLayout:
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(4)

        self.combo_comida = self._crear_combo()
        self.combo_horario = self._crear_combo()
        self.combo_objetivo = self._crear_combo()
        self._combos = (
            self.combo_comida,
            self.combo_horario,
            self.combo_objetivo,
        )

        etiquetas = (
            ("Comida", self.combo_comida),
            ("Horario", self.combo_horario),
            ("Objetivo general", self.combo_objetivo),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            filtros.addWidget(QLabel(texto), 0, columna)
            filtros.addWidget(combo, 1, columna)
            filtros.setColumnStretch(columna, 1)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "Buscar por comida, horario, alimento, objetivo u observaciones..."
        )
        self.busqueda.setClearButtonEnabled(True)
        self.busqueda.setMinimumWidth(240)
        filtros.addWidget(self.busqueda, 2, 0, 1, 3)

        self.boton_limpiar = QPushButton("Limpiar filtros")
        self.boton_limpiar.setToolTip("Limpiar todos los filtros (Ctrl+L)")
        filtros.addWidget(self.boton_limpiar, 2, 3)

        for combo in self._combos:
            combo.currentIndexChanged.connect(self._aplicar_filtros)
        self.busqueda.textChanged.connect(self._aplicar_filtros)
        self.boton_limpiar.clicked.connect(self._limpiar_filtros)

        self.atajo_limpiar = QShortcut(QKeySequence("Ctrl+L"), self)
        self.atajo_limpiar.setContext(Qt.WidgetWithChildrenShortcut)
        self.atajo_limpiar.activated.connect(self._limpiar_filtros)

        return filtros

    def _construir_contenido(self) -> QSplitter:
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSortingEnabled(True)
        self.tabla.sortByColumn(2, Qt.AscendingOrder)
        self.tabla.setWordWrap(False)
        self.tabla.verticalHeader().setVisible(False)

        encabezado = self.tabla.horizontalHeader()
        encabezado.setMinimumSectionSize(70)
        encabezado.setSectionResizeMode(QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(3, QHeaderView.Stretch)
        encabezado.setSectionResizeMode(5, QHeaderView.Stretch)
        encabezado.setStretchLastSection(False)

        self.tabla.selectionModel().currentRowChanged.connect(
            self._mostrar_detalle
        )

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.tabla)
        self.splitter.addWidget(self._construir_panel_detalle())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([780, 360])
        return self.splitter

    def _construir_panel_detalle(self) -> QGroupBox:
        panel = QGroupBox("Detalle de la comida")
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(430)

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        self.detalle_titulo = QLabel()
        fuente_titulo = self.detalle_titulo.font()
        fuente_titulo.setPointSize(13)
        fuente_titulo.setBold(True)
        self.detalle_titulo.setFont(fuente_titulo)
        self.detalle_titulo.setWordWrap(True)

        self.detalle_info = QLabel()
        self.detalle_info.setWordWrap(True)
        self.detalle_info.setTextFormat(Qt.PlainText)

        etiqueta_alimentos = QLabel("Alimentos sugeridos")
        fuente_alimentos = etiqueta_alimentos.font()
        fuente_alimentos.setBold(True)
        etiqueta_alimentos.setFont(fuente_alimentos)

        self.detalle_alimentos = QLabel()
        self.detalle_alimentos.setWordWrap(True)
        self.detalle_alimentos.setTextFormat(Qt.PlainText)

        etiqueta_observaciones = QLabel("Observaciones")
        fuente_observaciones = etiqueta_observaciones.font()
        fuente_observaciones.setBold(True)
        etiqueta_observaciones.setFont(fuente_observaciones)

        self.detalle_observaciones = QLabel()
        self.detalle_observaciones.setWordWrap(True)
        self.detalle_observaciones.setTextFormat(Qt.PlainText)

        layout.addWidget(self.detalle_titulo)
        layout.addWidget(self.detalle_info)
        layout.addSpacing(6)
        layout.addWidget(etiqueta_alimentos)
        layout.addWidget(self.detalle_alimentos)
        layout.addSpacing(6)
        layout.addWidget(etiqueta_observaciones)
        layout.addWidget(self.detalle_observaciones)
        layout.addStretch(1)

        self._limpiar_detalle()
        return panel

    @staticmethod
    def _crear_combo() -> QComboBox:
        combo = QComboBox()
        combo.setMinimumWidth(150)
        return combo

    def refrescar_datos(self, reiniciar_filtros: bool = False) -> None:
        self._cargar_combos(reiniciar=reiniciar_filtros)
        self._aplicar_filtros()
        self.actualizar_resumen()

    def actualizar_resumen(self) -> None:
        total = self.nutricion_service.total()
        if total == 0:
            self.etiqueta_resumen.setText("Plan nutricional no cargado")
            self.etiqueta_resumen.setToolTip(
                "Importa un plan de alimentación para consultar las comidas."
            )
            return

        alimentos = self.nutricion_service.alimentos_unicos()
        sugerencias = self.nutricion_service.total_sugerencias()
        self.etiqueta_resumen.setText(
            f"{total} comidas · {sugerencias} sugerencias · "
            f"{len(alimentos)} alimentos únicos"
        )
        if alimentos:
            self.etiqueta_resumen.setToolTip(
                "Alimentos únicos del plan:\n- " + "\n- ".join(alimentos)
            )
        else:
            self.etiqueta_resumen.setToolTip(
                "El plan no contiene alimentos sugeridos."
            )

    def _cargar_combos(self, reiniciar: bool) -> None:
        opciones = (
            (
                self.combo_comida,
                "Todas las comidas",
                self.nutricion_service.comidas(),
            ),
            (
                self.combo_horario,
                "Todos los horarios",
                self.nutricion_service.horarios(),
            ),
            (
                self.combo_objetivo,
                "Todos los objetivos",
                self.nutricion_service.objetivos(),
            ),
        )

        for combo, texto_todos, valores in opciones:
            anterior = "" if reiniciar else (combo.currentData() or "")
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(texto_todos, "")
            for valor in valores:
                combo.addItem(valor, valor)
            indice = combo.findData(anterior)
            combo.setCurrentIndex(indice if indice >= 0 else 0)
            combo.blockSignals(False)

        if reiniciar:
            self.busqueda.blockSignals(True)
            self.busqueda.clear()
            self.busqueda.blockSignals(False)

    def _aplicar_filtros(self, *_args: object) -> None:
        comidas = self.nutricion_service.filtrar(**self._filtros_actuales())

        cabecera = self.tabla.horizontalHeader()
        columna = cabecera.sortIndicatorSection()
        orden = cabecera.sortIndicatorOrder()

        self.modelo.set_registros(comidas)
        if self.tabla.isSortingEnabled() and columna >= 0:
            self.modelo.sort(columna, orden)

        self._actualizar_estado(len(comidas), self.nutricion_service.total())

        if self.modelo.rowCount():
            self.tabla.selectRow(0)
            self.tabla.setCurrentIndex(self.modelo.index(0, 0))
            self._mostrar_detalle()
        else:
            self._limpiar_detalle()

    def _filtros_actuales(self) -> dict[str, str]:
        return {
            "comida": self.combo_comida.currentData() or "",
            "horario": self.combo_horario.currentData() or "",
            "objetivo": self.combo_objetivo.currentData() or "",
            "texto": self.busqueda.text(),
        }

    def _limpiar_filtros(self) -> None:
        for combo in self._combos:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self.busqueda.blockSignals(True)
        self.busqueda.clear()
        self.busqueda.blockSignals(False)

        self._aplicar_filtros()

    def _mostrar_detalle(self, *_args: object) -> None:
        indice = self.tabla.currentIndex()
        if not indice.isValid():
            self._limpiar_detalle()
            return

        comida = self.modelo.registro_en(indice.row())
        if not isinstance(comida, Comida):
            self._limpiar_detalle()
            return

        self.detalle_titulo.setText(comida.comida)
        self.detalle_info.setText(
            "\n".join(
                (
                    f"ID: {comida.id_plan}",
                    f"Horario: {comida.horario}",
                    f"Objetivo: {comida.objetivo_general}",
                )
            )
        )
        self.detalle_alimentos.setText(
            "\n".join(f"- {alimento}" for alimento in comida.alimentos)
        )
        self.detalle_observaciones.setText(comida.observaciones)

    def _limpiar_detalle(self) -> None:
        self.detalle_titulo.setText("Sin comida seleccionada")
        self.detalle_info.setText(
            "Selecciona una fila del plan para ver sus alimentos y observaciones."
        )
        self.detalle_alimentos.setText("")
        self.detalle_observaciones.setText("")

    def _actualizar_estado(self, visibles: int, total: int) -> None:
        if total == 0:
            self.etiqueta_estado.setText(
                "No hay comidas cargadas. Usa «Importar plan CSV»."
            )
        elif visibles == 0:
            self.etiqueta_estado.setText(
                f"Sin coincidencias. 0 de {total} comidas."
            )
        elif visibles == total:
            if total == 1:
                self.etiqueta_estado.setText("1 comida cargada.")
            else:
                self.etiqueta_estado.setText(f"{total} comidas cargadas.")
        else:
            self.etiqueta_estado.setText(
                f"Mostrando {visibles} de {total} comidas."
            )
