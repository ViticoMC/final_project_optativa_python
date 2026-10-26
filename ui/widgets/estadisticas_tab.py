from PyQt5.QtCore import QAbstractItemModel, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService, Estadisticas
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService
from ui.models.table_models import (
    DistribucionTableModel,
    EjercicioRutinaTableModel,
)


class EstadisticasTab(QWidget):
    exportar_solicitado = pyqtSignal()

    def __init__(
        self,
        estadistica_service: EstadisticaService,
        rutina_service: RutinaService,
        ejercicio_service: EjercicioService,
        nutricion_service: NutricionService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.estadistica_service = estadistica_service
        self.rutina_service = rutina_service
        self.ejercicio_service = ejercicio_service
        self.nutricion_service = nutricion_service

        self.modelo_dias = DistribucionTableModel()
        self.modelo_grupos = DistribucionTableModel()
        self.modelo_niveles = DistribucionTableModel()
        self.modelo_series = DistribucionTableModel()
        self.modelo_catalogo = DistribucionTableModel()
        self.modelo_comidas = DistribucionTableModel()
        self.modelo_ejercicios = EjercicioRutinaTableModel()

        self._construir_ui()
        self.refrescar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addLayout(self._construir_cabecera())
        layout.addLayout(self._construir_tarjetas())
        layout.addWidget(self._construir_contenido(), 1)

    def _construir_cabecera(self) -> QHBoxLayout:
        cabecera = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(2)

        titulo = QLabel("Panel de estadísticas")
        fuente_titulo = titulo.font()
        fuente_titulo.setPointSize(16)
        fuente_titulo.setBold(True)
        titulo.setFont(fuente_titulo)

        subtitulo = QLabel(
            "Resumen del entrenamiento, del catálogo y del plan de "
            "alimentación a partir de los datos cargados."
        )
        subtitulo.setObjectName("subtitulo")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        self.boton_exportar = QPushButton("Exportar estadísticas CSV")
        self.boton_exportar.setToolTip(
            "Guardar un resumen de las estadísticas en un archivo CSV"
        )
        self.boton_exportar.clicked.connect(self.exportar_solicitado.emit)

        self.boton_actualizar = QPushButton("Actualizar")
        self.boton_actualizar.setToolTip("Recalcular las estadísticas")
        self.boton_actualizar.clicked.connect(self.refrescar_datos)

        cabecera.addLayout(textos)
        cabecera.addStretch(1)
        cabecera.addWidget(self.boton_exportar, 0, Qt.AlignTop)
        cabecera.addWidget(self.boton_actualizar, 0, Qt.AlignTop)
        return cabecera

    def _construir_tarjetas(self) -> QGridLayout:
        tarjetas = QGridLayout()
        tarjetas.setHorizontalSpacing(12)
        tarjetas.setVerticalSpacing(12)

        (
            self.valor_rutinas,
            self.detalle_rutinas,
        ) = self._crear_tarjeta(tarjetas, 0, "Rutinas")
        (
            self.valor_series,
            self.detalle_series,
        ) = self._crear_tarjeta(tarjetas, 1, "Series programadas")
        (
            self.valor_catalogo,
            self.detalle_catalogo,
        ) = self._crear_tarjeta(tarjetas, 2, "Catálogo")
        (
            self.valor_nutricion,
            self.detalle_nutricion,
        ) = self._crear_tarjeta(tarjetas, 3, "Nutrición")
        return tarjetas

    def _crear_tarjeta(
        self,
        layout: QGridLayout,
        columna: int,
        titulo: str,
    ) -> tuple[QLabel, QLabel]:
        marco = QFrame()
        marco.setFrameShape(QFrame.StyledPanel)
        marco.setObjectName("tarjeta_estadistica")

        contenido = QVBoxLayout(marco)
        contenido.setContentsMargins(12, 10, 12, 10)
        contenido.setSpacing(2)

        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setObjectName("titulo_tarjeta")

        valor = QLabel("0")
        fuente_valor = valor.font()
        fuente_valor.setPointSize(22)
        fuente_valor.setBold(True)
        valor.setFont(fuente_valor)

        detalle = QLabel()
        detalle.setWordWrap(True)
        detalle.setTextFormat(Qt.PlainText)
        detalle.setObjectName("detalle_tarjeta")

        contenido.addWidget(etiqueta_titulo)
        contenido.addWidget(valor)
        contenido.addWidget(detalle)

        layout.addWidget(marco, 0, columna)
        layout.setColumnStretch(columna, 1)
        return valor, detalle

    def _construir_contenido(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        contenido = QWidget()
        grid = QGridLayout(contenido)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.tabla_dias = self._crear_tabla(self.modelo_dias)
        self.tabla_grupos = self._crear_tabla(self.modelo_grupos)
        self.tabla_niveles = self._crear_tabla(self.modelo_niveles)
        self.tabla_series = self._crear_tabla(self.modelo_series)
        self.tabla_catalogo = self._crear_tabla(self.modelo_catalogo)
        self.tabla_comidas = self._crear_tabla(self.modelo_comidas)
        self.tabla_ejercicios = self._crear_tabla(
            self.modelo_ejercicios,
            altura=260,
        )

        grid.addWidget(
            self._crear_grupo("Rutinas por día", self.tabla_dias),
            0,
            0,
        )
        grid.addWidget(
            self._crear_grupo("Rutinas por grupo muscular", self.tabla_grupos),
            0,
            1,
        )
        grid.addWidget(
            self._crear_grupo("Rutinas por nivel", self.tabla_niveles),
            1,
            0,
        )
        grid.addWidget(
            self._crear_grupo("Series por grupo muscular", self.tabla_series),
            1,
            1,
        )
        grid.addWidget(
            self._crear_grupo("Catálogo por grupo", self.tabla_catalogo),
            2,
            0,
        )
        grid.addWidget(
            self._crear_grupo("Comidas por objetivo", self.tabla_comidas),
            2,
            1,
        )
        grid.addWidget(
            self._crear_grupo(
                "Ejercicios mencionados en las rutinas",
                self.tabla_ejercicios,
            ),
            3,
            0,
            1,
            2,
        )

        scroll.setWidget(contenido)
        return scroll

    @staticmethod
    def _crear_tabla(
        modelo: QAbstractItemModel,
        altura: int = 200,
    ) -> QTableView:
        tabla = QTableView()
        tabla.setModel(modelo)
        tabla.setAlternatingRowColors(True)
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.setSortingEnabled(False)
        tabla.setWordWrap(False)
        tabla.verticalHeader().setVisible(False)
        tabla.setMinimumHeight(altura)

        encabezado = tabla.horizontalHeader()
        encabezado.setMinimumSectionSize(70)
        encabezado.setSectionResizeMode(0, QHeaderView.Stretch)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        encabezado.setStretchLastSection(False)
        return tabla

    @staticmethod
    def _crear_grupo(titulo: str, tabla: QTableView) -> QGroupBox:
        grupo = QGroupBox(titulo)
        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(tabla)
        return grupo

    def refrescar_datos(self) -> None:
        estadisticas = self.estadistica_service.calcular(
            self.rutina_service.todas(),
            self.ejercicio_service.todos(),
            self.nutricion_service.todos(),
        )

        self.modelo_dias.set_registros(estadisticas.rutinas_por_dia)
        self.modelo_grupos.set_registros(estadisticas.rutinas_por_grupo)
        self.modelo_niveles.set_registros(estadisticas.rutinas_por_nivel)
        self.modelo_series.set_registros(estadisticas.series_por_grupo)
        self.modelo_catalogo.set_registros(
            estadisticas.catalogo_por_grupo
        )
        self.modelo_comidas.set_registros(
            estadisticas.comidas_por_objetivo
        )
        self.modelo_ejercicios.set_registros(
            estadisticas.ejercicios_rutinas
        )
        self._actualizar_tarjetas(estadisticas)

    def _actualizar_tarjetas(self, estadisticas: Estadisticas) -> None:
        self.valor_rutinas.setText(str(estadisticas.total_rutinas))
        self.detalle_rutinas.setText(
            f"{estadisticas.dias_entrenamiento} días activos · "
            f"{estadisticas.dias_descanso} de descanso"
        )

        self.valor_series.setText(str(estadisticas.total_series))
        self.detalle_series.setText(
            f"{estadisticas.promedio_series:.1f} series por rutina"
        )

        self.valor_catalogo.setText(str(estadisticas.total_ejercicios))
        cobertura = estadisticas.cobertura
        if cobertura.total:
            self.detalle_catalogo.setText(
                f"{len(cobertura.encontrados)}/{cobertura.total} de las "
                f"rutinas cubiertos ({cobertura.porcentaje:.1f} %)"
            )
        else:
            self.detalle_catalogo.setText("Sin ejercicios en las rutinas")

        self.valor_nutricion.setText(str(estadisticas.total_comidas))
        self.detalle_nutricion.setText(
            f"{estadisticas.alimentos_unicos} alimentos únicos · "
            f"{estadisticas.sugerencias} sugerencias"
        )
