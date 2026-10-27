from collections.abc import Iterable

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SelectorMultiple(QWidget):
    seleccion_cambiada = pyqtSignal()

    def __init__(
        self,
        titulo_disponibles: str = "Disponibles",
        titulo_seleccionados: str = "Seleccionados",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._disponibles: dict[str, str] = {}
        self._detalles: dict[str, str] = {}
        self._orden_disponibles: list[str] = []
        self._seleccionados: list[str] = []
        self._construir_ui(titulo_disponibles, titulo_seleccionados)
        self._refrescar_listas()

    def _construir_ui(
        self,
        titulo_disponibles: str,
        titulo_seleccionados: str,
    ) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        izquierda = QVBoxLayout()
        izquierda.setSpacing(4)
        izquierda.addWidget(QLabel(titulo_disponibles))

        self.lista_disponibles = QListWidget()
        self.lista_disponibles.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.lista_disponibles.setAlternatingRowColors(True)
        self.lista_disponibles.setMinimumHeight(220)
        self.lista_disponibles.setTextElideMode(Qt.ElideRight)
        self.lista_disponibles.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        izquierda.addWidget(self.lista_disponibles, 1)
        layout.addLayout(izquierda, 1)

        centro = QVBoxLayout()
        centro.setSpacing(6)
        centro.addStretch(1)

        self.boton_agregar = QPushButton("Añadir →")
        self.boton_agregar.setToolTip("Añadir el elemento seleccionado")
        self.boton_quitar = QPushButton("← Quitar")
        self.boton_quitar.setToolTip("Quitar los elementos seleccionados")
        self.boton_subir = QPushButton("Subir")
        self.boton_subir.setToolTip("Mover el elemento hacia arriba")
        self.boton_bajar = QPushButton("Bajar")
        self.boton_bajar.setToolTip("Mover el elemento hacia abajo")

        centro.addWidget(self.boton_agregar)
        centro.addWidget(self.boton_quitar)
        centro.addSpacing(10)
        centro.addWidget(self.boton_subir)
        centro.addWidget(self.boton_bajar)
        centro.addStretch(1)
        layout.addLayout(centro)

        derecha = QVBoxLayout()
        derecha.setSpacing(4)
        derecha.addWidget(QLabel(titulo_seleccionados))

        self.lista_seleccionados = QListWidget()
        self.lista_seleccionados.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.lista_seleccionados.setAlternatingRowColors(True)
        self.lista_seleccionados.setMinimumHeight(220)
        self.lista_seleccionados.setTextElideMode(Qt.ElideRight)
        self.lista_seleccionados.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        derecha.addWidget(self.lista_seleccionados, 1)
        layout.addLayout(derecha, 1)

        self.boton_agregar.clicked.connect(self._agregar_actual)
        self.boton_quitar.clicked.connect(self._quitar_actual)
        self.boton_subir.clicked.connect(lambda: self._mover(-1))
        self.boton_bajar.clicked.connect(lambda: self._mover(1))
        self.lista_disponibles.itemDoubleClicked.connect(
            lambda _item: self._agregar_actual()
        )
        self.lista_seleccionados.itemDoubleClicked.connect(
            lambda _item: self._quitar_actual()
        )
        self.lista_disponibles.itemSelectionChanged.connect(
            self._actualizar_botones
        )
        self.lista_seleccionados.itemSelectionChanged.connect(
            self._actualizar_botones
        )

    def set_disponibles(
        self,
        opciones: Iterable[tuple[str, str] | tuple[str, str, str] | str],
    ) -> None:
        self._disponibles.clear()
        self._detalles.clear()
        self._orden_disponibles.clear()
        for opcion in opciones:
            if isinstance(opcion, tuple):
                if len(opcion) >= 3:
                    valor, etiqueta, detalle = opcion[:3]
                else:
                    valor, etiqueta = opcion
                    detalle = etiqueta
            else:
                valor = etiqueta = detalle = str(opcion)
            valor = str(valor)
            if valor in self._disponibles:
                continue
            self._disponibles[valor] = str(etiqueta)
            self._detalles[valor] = str(detalle)
            self._orden_disponibles.append(valor)
        self._refrescar_listas()

    def set_seleccionados(self, valores: Iterable[str]) -> None:
        self._seleccionados = []
        for valor in valores:
            texto = str(valor)
            if texto and texto not in self._seleccionados:
                if texto not in self._disponibles:
                    self._disponibles[texto] = texto
                    self._detalles[texto] = texto
                    self._orden_disponibles.append(texto)
                self._seleccionados.append(texto)
        self._refrescar_listas()
        self.seleccion_cambiada.emit()

    def seleccionados(self) -> tuple[str, ...]:
        return tuple(self._seleccionados)

    def disponibles(self) -> tuple[str, ...]:
        return tuple(
            valor
            for valor in self._orden_disponibles
            if valor not in self._seleccionados
        )

    def agregar_valor(self, valor: str) -> None:
        texto = str(valor)
        if not texto or texto in self._seleccionados:
            return
        if texto not in self._disponibles:
            self._disponibles[texto] = texto
            self._detalles[texto] = texto
            self._orden_disponibles.append(texto)
        self._seleccionados.append(texto)
        self._refrescar_listas()
        self.seleccion_cambiada.emit()

    def limpiar_seleccion(self) -> None:
        if not self._seleccionados:
            return
        self._seleccionados = []
        self._refrescar_listas()
        self.seleccion_cambiada.emit()

    def _agregar_actual(self) -> None:
        item = self.lista_disponibles.currentItem()
        if item is None:
            return
        self.agregar_valor(str(item.data(Qt.UserRole)))

    def _quitar_actual(self) -> None:
        item = self.lista_seleccionados.currentItem()
        if item is None:
            return
        valor = str(item.data(Qt.UserRole))
        if valor not in self._seleccionados:
            return
        self._seleccionados.remove(valor)
        self._refrescar_listas()
        self.seleccion_cambiada.emit()

    def _mover(self, desplazamiento: int) -> None:
        item = self.lista_seleccionados.currentItem()
        if item is None:
            return
        valor = str(item.data(Qt.UserRole))
        try:
            posicion = self._seleccionados.index(valor)
        except ValueError:
            return
        destino = posicion + desplazamiento
        if not 0 <= destino < len(self._seleccionados):
            return
        self._seleccionados[posicion], self._seleccionados[destino] = (
            self._seleccionados[destino],
            self._seleccionados[posicion],
        )
        self._refrescar_listas()
        self.lista_seleccionados.setCurrentRow(destino)
        self.seleccion_cambiada.emit()

    def _refrescar_listas(self) -> None:
        disponibles = self.disponibles()

        self.lista_disponibles.blockSignals(True)
        self.lista_disponibles.clear()
        for valor in disponibles:
            item = QListWidgetItem(self._disponibles[valor])
            item.setData(Qt.UserRole, valor)
            item.setToolTip(self._detalles.get(valor, self._disponibles[valor]))
            self.lista_disponibles.addItem(item)
        self.lista_disponibles.blockSignals(False)

        self.lista_seleccionados.blockSignals(True)
        self.lista_seleccionados.clear()
        for valor in self._seleccionados:
            item = QListWidgetItem(self._disponibles.get(valor, valor))
            item.setData(Qt.UserRole, valor)
            item.setToolTip(self._detalles.get(valor, valor))
            self.lista_seleccionados.addItem(item)
        self.lista_seleccionados.blockSignals(False)
        self._actualizar_botones()

    def _actualizar_botones(self) -> None:
        self.boton_agregar.setEnabled(
            self.lista_disponibles.currentItem() is not None
        )
        self.boton_quitar.setEnabled(
            self.lista_seleccionados.currentItem() is not None
        )
        posicion = self.lista_seleccionados.currentRow()
        self.boton_subir.setEnabled(posicion > 0)
        self.boton_bajar.setEnabled(
            0 <= posicion < len(self._seleccionados) - 1
        )
