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

from app.models import Ejercicio
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService
from ui.models.table_models import EjercicioTableModel


class EjerciciosTab(QWidget):
    importar_solicitado = pyqtSignal()

    def __init__(
        self,
        ejercicio_service: EjercicioService,
        rutina_service: RutinaService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ejercicio_service = ejercicio_service
        self.rutina_service = rutina_service
        self.modelo = EjercicioTableModel()
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

        titulo = QLabel("Catálogo de ejercicios")
        fuente_titulo = titulo.font()
        fuente_titulo.setPointSize(16)
        fuente_titulo.setBold(True)
        titulo.setFont(fuente_titulo)

        subtitulo = QLabel(
            "Consulta la técnica, el equipamiento y la cobertura del catálogo "
            "respecto a tus rutinas."
        )
        subtitulo.setObjectName("subtitulo")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        derecha = QVBoxLayout()
        derecha.setSpacing(4)

        self.boton_importar = QPushButton("Importar catálogo CSV")
        self.boton_importar.setToolTip("Seleccionar un archivo CSV de ejercicios")
        self.boton_importar.clicked.connect(self.importar_solicitado.emit)

        self.etiqueta_cobertura = QLabel()
        self.etiqueta_cobertura.setWordWrap(True)
        self.etiqueta_cobertura.setAlignment(Qt.AlignRight)
        self.etiqueta_cobertura.setTextFormat(Qt.PlainText)

        derecha.addWidget(self.boton_importar, 0, Qt.AlignRight)
        derecha.addWidget(self.etiqueta_cobertura)

        cabecera.addLayout(textos)
        cabecera.addStretch(1)
        cabecera.addLayout(derecha)
        return cabecera

    def _construir_filtros(self) -> QGridLayout:
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(4)

        self.combo_grupo = self._crear_combo()
        self.combo_nivel = self._crear_combo()
        self.combo_patron = self._crear_combo()
        self.combo_equipo = self._crear_combo()
        self._combos = (
            self.combo_grupo,
            self.combo_nivel,
            self.combo_patron,
            self.combo_equipo,
        )

        etiquetas = (
            ("Grupo muscular", self.combo_grupo),
            ("Nivel sugerido", self.combo_nivel),
            ("Patrón de movimiento", self.combo_patron),
            ("Equipamiento", self.combo_equipo),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            filtros.addWidget(QLabel(texto), 0, columna)
            filtros.addWidget(combo, 1, columna)
            filtros.setColumnStretch(columna, 1)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "Buscar por nombre, grupo, patrón, equipamiento o nota técnica..."
        )
        self.busqueda.setClearButtonEnabled(True)
        self.busqueda.setMinimumWidth(240)
        filtros.addWidget(self.busqueda, 2, 0, 1, 4)

        self.boton_limpiar = QPushButton("Limpiar filtros")
        self.boton_limpiar.setToolTip("Limpiar todos los filtros (Ctrl+L)")
        filtros.addWidget(self.boton_limpiar, 2, 4)

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
        self.tabla.sortByColumn(0, Qt.AscendingOrder)
        self.tabla.setWordWrap(False)
        self.tabla.verticalHeader().setVisible(False)

        encabezado = self.tabla.horizontalHeader()
        encabezado.setMinimumSectionSize(70)
        encabezado.setSectionResizeMode(QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(1, QHeaderView.Stretch)
        encabezado.setSectionResizeMode(3, QHeaderView.Stretch)
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
        panel = QGroupBox("Ficha del ejercicio")
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

        etiqueta_nota = QLabel("Nota técnica")
        fuente_nota = etiqueta_nota.font()
        fuente_nota.setBold(True)
        etiqueta_nota.setFont(fuente_nota)

        self.detalle_nota = QLabel()
        self.detalle_nota.setWordWrap(True)
        self.detalle_nota.setTextFormat(Qt.PlainText)

        layout.addWidget(self.detalle_titulo)
        layout.addWidget(self.detalle_info)
        layout.addSpacing(6)
        layout.addWidget(etiqueta_nota)
        layout.addWidget(self.detalle_nota)
        layout.addStretch(1)

        self._limpiar_detalle()
        return panel

    @staticmethod
    def _crear_combo() -> QComboBox:
        combo = QComboBox()
        combo.setMinimumWidth(140)
        return combo

    def refrescar_datos(self, reiniciar_filtros: bool = False) -> None:
        self._cargar_combos(reiniciar=reiniciar_filtros)
        self._aplicar_filtros()
        self.actualizar_cobertura()

    def actualizar_cobertura(self) -> None:
        cobertura = self.ejercicio_service.cobertura(
            self.rutina_service.todas()
        )

        if self.ejercicio_service.total() == 0:
            self.etiqueta_cobertura.setText("Cobertura: catálogo no cargado")
            self.etiqueta_cobertura.setToolTip(
                "Importa un catálogo de ejercicios para calcular la cobertura."
            )
            return

        if cobertura.total == 0:
            self.etiqueta_cobertura.setText("Cobertura: sin rutinas cargadas")
            self.etiqueta_cobertura.setToolTip(
                "Carga rutinas para calcular la cobertura del catálogo."
            )
            return

        encontrados = len(cobertura.encontrados)
        self.etiqueta_cobertura.setText(
            f"Ejercicios de rutinas en catálogo: "
            f"{encontrados}/{cobertura.total} ({cobertura.porcentaje:.1f} %)"
        )

        if cobertura.faltantes:
            self.etiqueta_cobertura.setToolTip(
                "Ejercicios de las rutinas sin coincidencia en el catálogo:\n- "
                + "\n- ".join(cobertura.faltantes)
            )
        else:
            self.etiqueta_cobertura.setToolTip(
                "Todos los ejercicios de las rutinas están en el catálogo."
            )

    def _cargar_combos(self, reiniciar: bool) -> None:
        opciones = (
            (self.combo_grupo, "Todos los grupos", self.ejercicio_service.grupos()),
            (self.combo_nivel, "Todos los niveles", self.ejercicio_service.niveles()),
            (self.combo_patron, "Todos los patrones", self.ejercicio_service.patrones()),
            (
                self.combo_equipo,
                "Todos los equipos",
                self.ejercicio_service.equipamientos(),
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
        ejercicios = self.ejercicio_service.filtrar(**self._filtros_actuales())

        cabecera = self.tabla.horizontalHeader()
        columna = cabecera.sortIndicatorSection()
        orden = cabecera.sortIndicatorOrder()

        self.modelo.set_registros(ejercicios)
        if self.tabla.isSortingEnabled() and columna >= 0:
            self.modelo.sort(columna, orden)

        self._actualizar_estado(
            len(ejercicios),
            self.ejercicio_service.total(),
        )

        if self.modelo.rowCount():
            self.tabla.selectRow(0)
            self.tabla.setCurrentIndex(self.modelo.index(0, 0))
            self._mostrar_detalle()
        else:
            self._limpiar_detalle()

    def _filtros_actuales(self) -> dict[str, str]:
        return {
            "grupo": self.combo_grupo.currentData() or "",
            "nivel": self.combo_nivel.currentData() or "",
            "patron": self.combo_patron.currentData() or "",
            "equipo": self.combo_equipo.currentData() or "",
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

        ejercicio = self.modelo.registro_en(indice.row())
        if not isinstance(ejercicio, Ejercicio):
            self._limpiar_detalle()
            return

        self.detalle_titulo.setText(ejercicio.nombre)
        self.detalle_info.setText(
            "\n".join(
                (
                    f"ID: {ejercicio.id_ejercicio}",
                    f"Grupo muscular: {ejercicio.grupo_muscular}",
                    f"Patrón: {ejercicio.patron_movimiento}",
                    f"Equipamiento: {ejercicio.equipamiento}",
                    f"Nivel sugerido: {ejercicio.nivel_sugerido}",
                )
            )
        )
        self.detalle_nota.setText(ejercicio.nota_tecnica)

    def _limpiar_detalle(self) -> None:
        self.detalle_titulo.setText("Sin ejercicio seleccionado")
        self.detalle_info.setText(
            "Selecciona una fila del catálogo para ver su ficha técnica."
        )
        self.detalle_nota.setText("")

    def _actualizar_estado(self, visibles: int, total: int) -> None:
        if total == 0:
            self.etiqueta_estado.setText(
                "No hay ejercicios cargados. Usa «Importar catálogo CSV»."
            )
        elif visibles == 0:
            self.etiqueta_estado.setText(
                f"Sin coincidencias. 0 de {total} ejercicios."
            )
        elif visibles == total:
            if total == 1:
                self.etiqueta_estado.setText("1 ejercicio cargado.")
            else:
                self.etiqueta_estado.setText(f"{total} ejercicios cargados.")
        else:
            self.etiqueta_estado.setText(
                f"Mostrando {visibles} de {total} ejercicios."
            )
