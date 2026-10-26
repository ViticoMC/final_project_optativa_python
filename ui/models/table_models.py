from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models import Comida, Ejercicio, Rutina
from app.utils import clave_horario, normalizar_texto


def _formatear_lista(valor: object) -> str:
    if isinstance(valor, (list, tuple)):
        return "; ".join(str(elemento) for elemento in valor)
    return "" if valor is None else str(valor)


@dataclass(frozen=True)
class Columna:
    titulo: str
    atributo: str
    formato: Callable[[Any], str] | None = None
    clave_orden: Callable[[Any], Any] | None = None
    alineacion: int = int(Qt.AlignLeft | Qt.AlignVCenter)


class BaseTableModel(QAbstractTableModel):
    def __init__(
        self,
        columnas: Sequence[Columna],
        registros: Sequence[object] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._columnas = tuple(columnas)
        self._registros = list(registros)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._registros)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columnas)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        registro = self._registros[index.row()]
        columna = self._columnas[index.column()]

        if role == Qt.DisplayRole:
            return self._texto(registro, columna)
        if role == Qt.ToolTipRole:
            return self._texto(registro, columna)
        if role == Qt.UserRole:
            return registro
        if role == Qt.TextAlignmentRole:
            return columna.alineacion
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columnas):
                return self._columnas[section].titulo
            return None
        return section + 1

    def set_registros(self, registros: Sequence[object]) -> None:
        self.beginResetModel()
        self._registros = list(registros)
        self.endResetModel()

    def registros(self) -> tuple[object, ...]:
        return tuple(self._registros)

    def registro_en(self, fila: int) -> object | None:
        if 0 <= fila < len(self._registros):
            return self._registros[fila]
        return None

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.AscendingOrder,
    ) -> None:
        if not 0 <= column < len(self._columnas):
            return

        columna = self._columnas[column]
        self.beginResetModel()
        self._registros.sort(
            key=lambda registro: self._clave_orden(registro, columna),
            reverse=order == Qt.DescendingOrder,
        )
        self.endResetModel()

    def _texto(self, registro: object, columna: Columna) -> str:
        valor = getattr(registro, columna.atributo)
        if columna.formato is not None:
            return columna.formato(valor)
        if isinstance(valor, (list, tuple)):
            return "; ".join(str(elemento) for elemento in valor)
        return "" if valor is None else str(valor)

    def _clave_orden(self, registro: object, columna: Columna) -> Any:
        valor = getattr(registro, columna.atributo)
        if columna.clave_orden is not None:
            return columna.clave_orden(valor)
        if isinstance(valor, (int, float)):
            return valor
        if isinstance(valor, (list, tuple)):
            return normalizar_texto("; ".join(str(elemento) for elemento in valor))
        return normalizar_texto(valor)


class RutinaTableModel(BaseTableModel):
    COLUMNAS = (
        Columna("ID", "id_rutina"),
        Columna("Día", "dia"),
        Columna("Horario", "horario"),
        Columna("Grupo muscular", "grupo_muscular"),
        Columna("Ejercicios", "ejercicios", formato=_formatear_lista),
        Columna("Series", "series", alineacion=int(Qt.AlignCenter)),
        Columna("Repeticiones / duración", "repeticiones"),
        Columna("Nivel", "nivel"),
        Columna("Descanso", "descanso"),
    )

    def __init__(
        self,
        rutinas: Sequence[Rutina] = (),
        parent=None,
    ) -> None:
        super().__init__(self.COLUMNAS, rutinas, parent)


class EjercicioTableModel(BaseTableModel):
    COLUMNAS = (
        Columna("ID", "id_ejercicio"),
        Columna("Nombre", "nombre"),
        Columna("Grupo muscular", "grupo_muscular"),
        Columna("Patrón de movimiento", "patron_movimiento"),
        Columna("Equipamiento", "equipamiento"),
        Columna("Nivel sugerido", "nivel_sugerido"),
    )

    def __init__(
        self,
        ejercicios: Sequence[Ejercicio] = (),
        parent=None,
    ) -> None:
        super().__init__(self.COLUMNAS, ejercicios, parent)


class ComidaTableModel(BaseTableModel):
    COLUMNAS = (
        Columna("ID", "id_plan"),
        Columna("Comida", "comida"),
        Columna("Horario", "horario", clave_orden=clave_horario),
        Columna(
            "Alimentos sugeridos",
            "alimentos",
            formato=_formatear_lista,
        ),
        Columna("Objetivo", "objetivo_general"),
        Columna("Observaciones", "observaciones"),
    )

    def __init__(
        self,
        comidas: Sequence[Comida] = (),
        parent=None,
    ) -> None:
        super().__init__(self.COLUMNAS, comidas, parent)
