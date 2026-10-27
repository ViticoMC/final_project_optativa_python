from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from app.exceptions import FitPlanError
from app.models import Comida, PlantillaRutina, Rutina
from app.utils import normalizar_texto
from services.comida_personal_service import ComidaPersonalService
from services.plantilla_service import PlantillaService
from ui.dialogs import mostrar_error
from ui.widgets.selector_multiple import SelectorMultiple


class DialogoPlantillaRutina(QDialog):
    def __init__(
        self,
        servicio: PlantillaService,
        plantilla: PlantillaRutina | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.plantilla = plantilla
        self.resultado: PlantillaRutina | None = None
        self._construir_ui()
        self._cargar_opciones()
        self._conectar_filtros()
        self._actualizar_disponibles()
        if plantilla is not None:
            self._precargar(plantilla)
        else:
            self._actualizar_grupo()

    def _construir_ui(self) -> None:
        self.setWindowTitle(
            "Editar plantilla" if self.plantilla else "Nueva plantilla"
        )
        self.resize(920, 650)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        titulo = QLabel(
            "Editar mi plantilla"
            if self.plantilla
            else "Crear una plantilla con ejercicios del catálogo"
        )
        fuente = titulo.font()
        fuente.setPointSize(14)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Todos los ejercicios y valores se eligen de los CSV estándar. "
            "No se escriben datos nuevos."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.grupo_base = self._construir_base()
        self.grupo_base.setVisible(self.plantilla is None)
        layout.addWidget(self.grupo_base)

        self.etiqueta_aviso = QLabel()
        self.etiqueta_aviso.setObjectName("subtitulo")
        self.etiqueta_aviso.setWordWrap(True)
        self.etiqueta_aviso.setVisible(False)
        layout.addWidget(self.etiqueta_aviso)

        layout.addLayout(self._construir_filtros())
        grupo_prescripcion = self._construir_prescripcion()
        layout.addWidget(self.grupo_selector, 1)
        layout.addWidget(grupo_prescripcion)

        self.etiqueta_grupo = QLabel()
        self.etiqueta_grupo.setObjectName("estado_tabla")
        layout.addWidget(self.etiqueta_grupo)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.botones.button(QDialogButtonBox.Save).setText("Guardar")
        self.botones.button(QDialogButtonBox.Save).setObjectName(
            "boton_primario"
        )
        self.botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

    def _construir_base(self) -> QGroupBox:
        grupo = QGroupBox("Punto de partida opcional")
        layout = QHBoxLayout(grupo)
        layout.addWidget(QLabel("Copiar ejercicios de una rutina estándar:"))
        self.combo_base = QComboBox()
        self.combo_base.setMinimumWidth(360)
        layout.addWidget(self.combo_base, 1)
        self.combo_base.currentIndexChanged.connect(self._cargar_desde_base)
        return grupo

    def _construir_filtros(self) -> QGridLayout:
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(4)

        self.combo_grupo = QComboBox()
        self.combo_patron = QComboBox()
        self.combo_equipo = QComboBox()
        self.combo_nivel = QComboBox()
        self._combos_filtro = (
            self.combo_grupo,
            self.combo_patron,
            self.combo_equipo,
            self.combo_nivel,
        )

        etiquetas = (
            ("Grupo muscular", self.combo_grupo),
            ("Patrón", self.combo_patron),
            ("Equipamiento", self.combo_equipo),
            ("Nivel", self.combo_nivel),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            combo.setMinimumWidth(150)
            filtros.addWidget(QLabel(texto), 0, columna)
            filtros.addWidget(combo, 1, columna)
            filtros.setColumnStretch(columna, 1)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "Filtrar ejercicios disponibles por nombre, nota técnica..."
        )
        self.busqueda.setClearButtonEnabled(True)
        filtros.addWidget(self.busqueda, 2, 0, 1, 4)
        return filtros

    def _construir_prescripcion(self) -> QGroupBox:
        grupo = QGroupBox("Prescripción y selección")
        layout = QGridLayout(grupo)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)

        self.combo_series = QComboBox()
        self.combo_repeticiones = QComboBox()
        self.combo_descanso = QComboBox()
        self.combo_nivel_plantilla = QComboBox()

        self.grupo_selector = QGroupBox("Ejercicios de la plantilla")
        selector_layout = QVBoxLayout(self.grupo_selector)
        self.selector = SelectorMultiple(
            "Catálogo disponible",
            "Ejercicios seleccionados",
        )
        self.selector.seleccion_cambiada.connect(self._actualizar_grupo)
        selector_layout.addWidget(self.selector)

        etiquetas = (
            ("Series", self.combo_series),
            ("Repeticiones / duración", self.combo_repeticiones),
            ("Descanso", self.combo_descanso),
            ("Nivel", self.combo_nivel_plantilla),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            combo.setMinimumWidth(150)
            layout.addWidget(QLabel(texto), 0, columna)
            layout.addWidget(combo, 1, columna)
            layout.setColumnStretch(columna, 1)
        return grupo

    def _cargar_opciones(self) -> None:
        self._cargar_combo(
            self.combo_grupo,
            "Todos los grupos",
            self.servicio.grupos_ejercicio(),
        )
        self._cargar_combo(
            self.combo_patron,
            "Todos los patrones",
            self.servicio.patrones_ejercicio(),
        )
        self._cargar_combo(
            self.combo_equipo,
            "Todos los equipamientos",
            self.servicio.equipamientos_ejercicio(),
        )
        self._cargar_combo(
            self.combo_nivel,
            "Todos los niveles",
            self.servicio.niveles_ejercicio(),
        )

        self.combo_series.clear()
        for valor in self.servicio.opciones_series():
            self.combo_series.addItem(str(valor), valor)

        self._cargar_combo(
            self.combo_repeticiones,
            "Elegir repeticiones",
            self.servicio.opciones_repeticiones(),
        )
        self._cargar_combo(
            self.combo_descanso,
            "Elegir descanso",
            self.servicio.opciones_descanso(),
        )
        self._cargar_combo(
            self.combo_nivel_plantilla,
            "Elegir nivel",
            self.servicio.opciones_nivel(),
        )

        self.combo_base.clear()
        self.combo_base.addItem("Selección manual", "")
        for rutina in self.servicio.rutinas_estandar():
            texto = (
                f"{rutina.id_rutina} · {rutina.dia} · "
                f"{rutina.grupo_muscular} · {rutina.horario}"
            )
            self.combo_base.addItem(texto, rutina.id_rutina)

    @staticmethod
    def _cargar_combo(
        combo: QComboBox,
        texto_inicial: str,
        valores: list[str],
    ) -> None:
        combo.clear()
        combo.addItem(texto_inicial, "")
        for valor in valores:
            combo.addItem(valor, valor)
        combo.setCurrentIndex(0)

    def _conectar_filtros(self) -> None:
        for combo in self._combos_filtro:
            combo.currentIndexChanged.connect(self._actualizar_disponibles)
        self.busqueda.textChanged.connect(self._actualizar_disponibles)

    def _actualizar_disponibles(self, *_args: object) -> None:
        ejercicios = self.servicio.ejercicios_disponibles(
            grupo=self.combo_grupo.currentData() or "",
            patron=self.combo_patron.currentData() or "",
            equipo=self.combo_equipo.currentData() or "",
            nivel=self.combo_nivel.currentData() or "",
            texto=self.busqueda.text(),
        )
        self.selector.set_disponibles(
            (
                ejercicio.nombre,
                ejercicio.nombre,
                f"{ejercicio.nombre} · {ejercicio.grupo_muscular} · "
                f"{ejercicio.equipamiento} · {ejercicio.nivel_sugerido}",
            )
            for ejercicio in ejercicios
        )

    def _cargar_desde_base(self, *_args: object) -> None:
        if self.plantilla is not None:
            return
        id_rutina = self.combo_base.currentData() or ""
        if not id_rutina:
            return

        rutina = next(
            (
                registro
                for registro in self.servicio.rutinas_estandar()
                if registro.id_rutina == id_rutina
            ),
            None,
        )
        if rutina is None:
            return
        self._aplicar_rutina(rutina)

    def _aplicar_rutina(self, rutina: Rutina) -> None:
        catalogo = {
            normalizar_texto(ejercicio.nombre): ejercicio.nombre
            for ejercicio in self.servicio.catalogo.todos()
        }
        seleccionados: list[str] = []
        omitidos: list[str] = []
        for nombre in rutina.ejercicios:
            canonico = catalogo.get(normalizar_texto(nombre))
            if canonico is None:
                omitidos.append(nombre)
            else:
                seleccionados.append(canonico)

        self.selector.set_seleccionados(seleccionados)
        if omitidos:
            self.etiqueta_aviso.setText(
                "Se omitieron ejercicios de la rutina estándar que no están "
                "en el catálogo: " + ", ".join(omitidos) + "."
            )
            self.etiqueta_aviso.setVisible(True)
        else:
            self.etiqueta_aviso.setVisible(False)

        self._seleccionar_por_dato(self.combo_series, rutina.series)
        self._seleccionar_por_texto(
            self.combo_repeticiones,
            rutina.repeticiones,
        )
        self._seleccionar_por_texto(self.combo_descanso, rutina.descanso)
        self._seleccionar_por_texto(
            self.combo_nivel_plantilla,
            rutina.nivel,
        )

    def _precargar(self, plantilla: PlantillaRutina) -> None:
        self.selector.set_seleccionados(plantilla.ejercicios)
        self._seleccionar_por_dato(self.combo_series, plantilla.series)
        self._seleccionar_por_texto(
            self.combo_repeticiones,
            plantilla.repeticiones,
        )
        self._seleccionar_por_texto(self.combo_descanso, plantilla.descanso)
        self._seleccionar_por_texto(
            self.combo_nivel_plantilla,
            plantilla.nivel,
        )
        self._actualizar_grupo()

    @staticmethod
    def _seleccionar_por_dato(combo: QComboBox, valor: object) -> None:
        indice = combo.findData(valor)
        if indice >= 0:
            combo.setCurrentIndex(indice)

    @staticmethod
    def _seleccionar_por_texto(combo: QComboBox, valor: str) -> None:
        indice = combo.findData(valor)
        if indice < 0:
            indice = combo.findText(valor, Qt.MatchFixedString)
        if indice < 0 and valor:
            combo.addItem(valor, valor)
            indice = combo.count() - 1
        if indice >= 0:
            combo.setCurrentIndex(indice)

    def _actualizar_grupo(self) -> None:
        seleccionados = self.selector.seleccionados()
        if not seleccionados:
            self.etiqueta_grupo.setText(
                "Añade al menos un ejercicio para crear la plantilla."
            )
            return
        try:
            grupo = self.servicio.grupo_para(seleccionados)
        except FitPlanError as exc:
            self.etiqueta_grupo.setText(str(exc))
            return
        self.etiqueta_grupo.setText(
            f"Grupo resultante: {grupo} · "
            f"{len(seleccionados)} ejercicio(s) seleccionado(s)."
        )

    def datos_actuales(self) -> dict[str, object]:
        return {
            "ejercicios": self.selector.seleccionados(),
            "series": self.combo_series.currentData(),
            "repeticiones": self.combo_repeticiones.currentData(),
            "nivel": self.combo_nivel_plantilla.currentData(),
            "descanso": self.combo_descanso.currentData(),
        }

    def accept(self) -> None:
        datos = self.datos_actuales()
        try:
            if self.plantilla is None:
                self.resultado = self.servicio.crear(
                    datos["ejercicios"],
                    datos["series"],
                    datos["repeticiones"],
                    datos["nivel"],
                    datos["descanso"],
                )
            else:
                self.resultado = self.servicio.actualizar(
                    self.plantilla.id_plantilla,
                    datos["ejercicios"],
                    datos["series"],
                    datos["repeticiones"],
                    datos["nivel"],
                    datos["descanso"],
                )
        except FitPlanError as exc:
            mostrar_error(
                self,
                "No se pudo guardar la plantilla",
                exc,
            )
            return
        super().accept()


class DialogoComidaPersonal(QDialog):
    def __init__(
        self,
        servicio: ComidaPersonalService,
        comida: Comida | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.comida = comida
        self.resultado: Comida | None = None
        self._construir_ui()
        self._cargar_opciones()
        self._conectar_filtros()
        self._actualizar_disponibles()
        if comida is not None:
            self._precargar(comida)

    def _construir_ui(self) -> None:
        self.setWindowTitle(
            "Editar comida" if self.comida else "Nueva comida"
        )
        self.resize(900, 640)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        titulo = QLabel(
            "Editar mi comida"
            if self.comida
            else "Crear una comida con alimentos del plan estándar"
        )
        fuente = titulo.font()
        fuente.setPointSize(14)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "El tipo, horario, objetivo y alimentos se eligen de los datos "
            "estándar. No se escriben alimentos nuevos."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.grupo_base = self._construir_base()
        self.grupo_base.setVisible(self.comida is None)
        layout.addWidget(self.grupo_base)

        layout.addWidget(self._construir_formulario())
        layout.addLayout(self._construir_filtros())
        layout.addWidget(self.grupo_selector, 1)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.botones.button(QDialogButtonBox.Save).setText("Guardar")
        self.botones.button(QDialogButtonBox.Save).setObjectName(
            "boton_primario"
        )
        self.botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

    def _construir_base(self) -> QGroupBox:
        grupo = QGroupBox("Punto de partida opcional")
        layout = QHBoxLayout(grupo)
        layout.addWidget(QLabel("Copiar alimentos de una comida estándar:"))
        self.combo_base = QComboBox()
        self.combo_base.setMinimumWidth(360)
        layout.addWidget(self.combo_base, 1)
        self.combo_base.currentIndexChanged.connect(self._cargar_desde_base)
        return grupo

    def _construir_formulario(self) -> QGroupBox:
        grupo = QGroupBox("Datos de la comida")
        layout = QGridLayout(grupo)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)

        self.combo_comida = QComboBox()
        self.combo_horario = QComboBox()
        self.combo_objetivo = QComboBox()
        etiquetas = (
            ("Comida", self.combo_comida),
            ("Horario", self.combo_horario),
            ("Objetivo general", self.combo_objetivo),
        )
        for columna, (texto, combo) in enumerate(etiquetas):
            combo.setMinimumWidth(180)
            layout.addWidget(QLabel(texto), 0, columna)
            layout.addWidget(combo, 1, columna)
            layout.setColumnStretch(columna, 1)
        return grupo

    def _construir_filtros(self) -> QGridLayout:
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(4)

        self.combo_origen = QComboBox()
        self.combo_origen.setMinimumWidth(220)
        filtros.addWidget(QLabel("Filtrar alimentos por comida de origen"), 0, 0)
        filtros.addWidget(self.combo_origen, 1, 0)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Filtrar alimentos disponibles...")
        self.busqueda.setClearButtonEnabled(True)
        filtros.addWidget(self.busqueda, 1, 1)
        filtros.setColumnStretch(1, 1)

        self.grupo_selector = QGroupBox("Alimentos de mi comida")
        selector_layout = QVBoxLayout(self.grupo_selector)
        self.selector = SelectorMultiple(
            "Alimentos estándar",
            "Alimentos seleccionados",
        )
        selector_layout.addWidget(self.selector)
        return filtros

    def _cargar_opciones(self) -> None:
        self._cargar_combo(
            self.combo_comida,
            "Elegir comida",
            self.servicio.tipos_comida(),
        )
        self._cargar_combo(
            self.combo_horario,
            "Elegir horario",
            self.servicio.horarios(),
        )
        self._cargar_combo(
            self.combo_objetivo,
            "Elegir objetivo",
            self.servicio.objetivos(),
        )
        self._cargar_combo(
            self.combo_origen,
            "Todas las comidas de origen",
            self.servicio.tipos_comida(),
        )

        self.combo_base.clear()
        self.combo_base.addItem("Selección manual", "")
        for comida in self.servicio.comidas_estandar():
            self.combo_base.addItem(
                f"{comida.id_plan} · {comida.comida} · {comida.horario}",
                comida.id_plan,
            )

    @staticmethod
    def _cargar_combo(
        combo: QComboBox,
        texto_inicial: str,
        valores: list[str],
    ) -> None:
        combo.clear()
        combo.addItem(texto_inicial, "")
        for valor in valores:
            combo.addItem(valor, valor)
        combo.setCurrentIndex(0)

    def _conectar_filtros(self) -> None:
        self.combo_origen.currentIndexChanged.connect(
            self._actualizar_disponibles
        )
        self.busqueda.textChanged.connect(self._actualizar_disponibles)

    def _actualizar_disponibles(self, *_args: object) -> None:
        origen = self.combo_origen.currentData() or ""
        alimentos = self.servicio.alimentos_por_comida(origen)
        filtro = normalizar_texto(self.busqueda.text())
        if filtro:
            alimentos = [
                alimento
                for alimento in alimentos
                if filtro in normalizar_texto(alimento)
            ]
        self.selector.set_disponibles(alimentos)

    def _cargar_desde_base(self, *_args: object) -> None:
        if self.comida is not None:
            return
        id_comida = self.combo_base.currentData() or ""
        if not id_comida:
            return
        registro = next(
            (
                comida
                for comida in self.servicio.comidas_estandar()
                if comida.id_plan == id_comida
            ),
            None,
        )
        if registro is None:
            return
        self._aplicar_comida(registro)

    def _aplicar_comida(self, comida: Comida) -> None:
        self._seleccionar_por_texto(self.combo_comida, comida.comida)
        self._seleccionar_por_texto(self.combo_horario, comida.horario)
        self._seleccionar_por_texto(
            self.combo_objetivo,
            comida.objetivo_general,
        )
        self.selector.set_seleccionados(comida.alimentos)

    def _precargar(self, comida: Comida) -> None:
        self._aplicar_comida(comida)

    @staticmethod
    def _seleccionar_por_texto(combo: QComboBox, valor: str) -> None:
        indice = combo.findData(valor)
        if indice < 0:
            indice = combo.findText(valor, Qt.MatchFixedString)
        if indice < 0 and valor:
            combo.addItem(valor, valor)
            indice = combo.count() - 1
        if indice >= 0:
            combo.setCurrentIndex(indice)

    def datos_actuales(self) -> dict[str, object]:
        return {
            "comida": self.combo_comida.currentData(),
            "horario": self.combo_horario.currentData(),
            "alimentos": self.selector.seleccionados(),
            "objetivo": self.combo_objetivo.currentData(),
        }

    def accept(self) -> None:
        datos = self.datos_actuales()
        try:
            if self.comida is None:
                self.resultado = self.servicio.crear(
                    datos["comida"],
                    datos["horario"],
                    datos["alimentos"],
                    datos["objetivo"],
                )
            else:
                self.resultado = self.servicio.actualizar(
                    self.comida.id_plan,
                    datos["comida"],
                    datos["horario"],
                    datos["alimentos"],
                    datos["objetivo"],
                )
        except FitPlanError as exc:
            mostrar_error(
                self,
                "No se pudo guardar la comida",
                exc,
            )
            return
        super().accept()
