from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QShortcut,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.models import Rutina
from services.rutina_service import RutinaService
from ui.models.table_models import RutinaTableModel


class RutinasTab(QWidget):
    importar_solicitado = pyqtSignal()
    exportar_solicitado = pyqtSignal()

    def __init__(self, rutina_service: RutinaService, parent=None) -> None:
        super().__init__(parent)
        self.rutina_service = rutina_service
        self.modelo = RutinaTableModel()
        self._construir_ui()
        self.refrescar_datos(reiniciar_filtros=True)

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addLayout(self._construir_cabecera())
        layout.addLayout(self._construir_filtros())
        layout.addWidget(self._construir_tabla(), 1)

        self.etiqueta_estado = QLabel()
        self.etiqueta_estado.setObjectName("estado_tabla")
        layout.addWidget(self.etiqueta_estado)

    def _construir_cabecera(self) -> QHBoxLayout:
        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)

        titulo = QLabel("Rutinas de entrenamiento")
        fuente_titulo = titulo.font()
        fuente_titulo.setPointSize(16)
        fuente_titulo.setBold(True)
        titulo.setFont(fuente_titulo)

        subtitulo = QLabel(
            "Filtra por día, grupo, nivel u horario; usa la búsqueda libre. "
            "Haz clic en una cabecera para ordenar."
        )
        subtitulo.setObjectName("subtitulo")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        self.boton_exportar = QPushButton("Exportar vista CSV")
        self.boton_exportar.setToolTip(
            "Exportar las rutinas visibles con los filtros actuales"
        )
        self.boton_exportar.clicked.connect(self.exportar_solicitado.emit)

        self.boton_importar = QPushButton("Importar CSV")
        self.boton_importar.setToolTip("Seleccionar un archivo CSV de rutinas")
        self.boton_importar.clicked.connect(self.importar_solicitado.emit)

        cabecera.addLayout(textos)
        cabecera.addStretch(1)
        cabecera.addWidget(self.boton_exportar)
        cabecera.addWidget(self.boton_importar)
        return cabecera

    def _construir_filtros(self) -> QGridLayout:
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(4)

        self.combo_dia = self._crear_combo()
        self.combo_grupo = self._crear_combo()
        self.combo_nivel = self._crear_combo()
        self.combo_horario = self._crear_combo()
        self._combos = (
            self.combo_dia,
            self.combo_grupo,
            self.combo_nivel,
            self.combo_horario,
        )

        etiquetas = (
            ("Día", self.combo_dia),
            ("Grupo muscular", self.combo_grupo),
            ("Nivel", self.combo_nivel),
            ("Horario", self.combo_horario),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            filtros.addWidget(QLabel(texto), 0, columna)
            filtros.addWidget(combo, 1, columna)
            filtros.setColumnStretch(columna, 1)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "Buscar por ID, día, grupo, ejercicio, nivel, horario..."
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

    def _construir_tabla(self) -> QTableView:
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
        encabezado.setSectionResizeMode(4, QHeaderView.Stretch)
        encabezado.setStretchLastSection(False)
        return self.tabla

    @staticmethod
    def _crear_combo() -> QComboBox:
        combo = QComboBox()
        combo.setMinimumWidth(140)
        return combo

    def registros_visibles(self) -> tuple[Rutina, ...]:
        return tuple(
            registro
            for registro in self.modelo.registros()
            if isinstance(registro, Rutina)
        )

    def refrescar_datos(self, reiniciar_filtros: bool = False) -> None:
        self._cargar_combos(reiniciar=reiniciar_filtros)
        self._aplicar_filtros()

    def _cargar_combos(self, reiniciar: bool) -> None:
        opciones = (
            (self.combo_dia, "Todos los días", self.rutina_service.dias()),
            (self.combo_grupo, "Todos los grupos", self.rutina_service.grupos()),
            (self.combo_nivel, "Todos los niveles", self.rutina_service.niveles()),
            (self.combo_horario, "Todos los horarios", self.rutina_service.horarios()),
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
        rutinas = self.rutina_service.filtrar(**self._filtros_actuales())

        cabecera = self.tabla.horizontalHeader()
        columna = cabecera.sortIndicatorSection()
        orden = cabecera.sortIndicatorOrder()

        self.modelo.set_registros(rutinas)
        if self.tabla.isSortingEnabled() and columna >= 0:
            self.modelo.sort(columna, orden)

        self._actualizar_estado(len(rutinas), self.rutina_service.total())

    def _filtros_actuales(self) -> dict[str, str]:
        return {
            "dia": self.combo_dia.currentData() or "",
            "grupo": self.combo_grupo.currentData() or "",
            "nivel": self.combo_nivel.currentData() or "",
            "horario": self.combo_horario.currentData() or "",
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

    def _actualizar_estado(self, visibles: int, total: int) -> None:
        if total == 0:
            self.etiqueta_estado.setText(
                "No hay rutinas cargadas. Usa «Importar CSV» o el menú Archivo."
            )
        elif visibles == 0:
            self.etiqueta_estado.setText(
                f"Sin coincidencias. 0 de {total} rutinas."
            )
        elif visibles == total:
            if total == 1:
                self.etiqueta_estado.setText("1 rutina cargada.")
            else:
                self.etiqueta_estado.setText(f"{total} rutinas cargadas.")
        else:
            self.etiqueta_estado.setText(
                f"Mostrando {visibles} de {total} rutinas."
            )
