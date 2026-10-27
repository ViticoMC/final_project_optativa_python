from collections.abc import Mapping
from dataclasses import dataclass

from app.exceptions import DataValidationError
from app.utils import a_entero, dividir_lista, normalizar_texto


def _campo(fila: Mapping[str, object], nombre: str, contexto: str) -> str:
    valor = "" if fila.get(nombre) is None else str(fila[nombre]).strip()
    if not valor:
        raise DataValidationError(
            f"{contexto}: falta el campo obligatorio '{nombre}'."
        )
    return valor


@dataclass(frozen=True, slots=True)
class Rutina:
    id_rutina: str
    dia: str
    horario: str
    grupo_muscular: str
    ejercicios: tuple[str, ...]
    series: int
    repeticiones: str
    nivel: str
    descanso: str

    @classmethod
    def from_row(cls, fila: Mapping[str, object]) -> "Rutina":
        id_rutina = _campo(fila, "id_rutina", "Rutina")
        contexto = f"Rutina {id_rutina}"
        series_texto = _campo(fila, "series", contexto)
        series = a_entero(series_texto, defecto=-1)
        if series < 0:
            raise DataValidationError(
                f"{contexto}: el valor de series no es válido: {series_texto!r}."
            )
        ejercicios = dividir_lista(_campo(fila, "ejercicios", contexto))
        if not ejercicios:
            raise DataValidationError(
                f"{contexto}: debe incluir al menos un ejercicio."
            )
        return cls(
            id_rutina=id_rutina,
            dia=_campo(fila, "dia", contexto),
            horario=_campo(fila, "horario", contexto),
            grupo_muscular=_campo(fila, "grupo_muscular", contexto),
            ejercicios=ejercicios,
            series=series,
            repeticiones=_campo(fila, "repeticiones_o_duracion", contexto),
            nivel=_campo(fila, "nivel", contexto),
            descanso=_campo(fila, "descanso", contexto),
        )

    @property
    def es_descanso(self) -> bool:
        return self.series == 0 or "descanso" in normalizar_texto(self.horario)

    @property
    def num_ejercicios(self) -> int:
        return len(self.ejercicios)

    def to_row(self) -> dict[str, str]:
        return {
            "id_rutina": self.id_rutina,
            "dia": self.dia,
            "horario": self.horario,
            "grupo_muscular": self.grupo_muscular,
            "ejercicios": "; ".join(self.ejercicios),
            "series": str(self.series),
            "repeticiones_o_duracion": self.repeticiones,
            "nivel": self.nivel,
            "descanso": self.descanso,
        }


@dataclass(frozen=True, slots=True)
class PlantillaRutina:
    id_plantilla: str
    grupo_muscular: str
    ejercicios: tuple[str, ...]
    series: int
    repeticiones: str
    nivel: str
    descanso: str

    @classmethod
    def from_row(cls, fila: Mapping[str, object]) -> "PlantillaRutina":
        id_plantilla = _campo(fila, "id_plantilla", "Plantilla")
        contexto = f"Plantilla {id_plantilla}"
        series_texto = _campo(fila, "series", contexto)
        series = a_entero(series_texto, defecto=-1)
        if series <= 0:
            raise DataValidationError(
                f"{contexto}: el valor de series no es válido: {series_texto!r}."
            )
        ejercicios = dividir_lista(_campo(fila, "ejercicios", contexto))
        if not ejercicios:
            raise DataValidationError(
                f"{contexto}: debe incluir al menos un ejercicio."
            )
        return cls(
            id_plantilla=id_plantilla,
            grupo_muscular=_campo(fila, "grupo_muscular", contexto),
            ejercicios=ejercicios,
            series=series,
            repeticiones=_campo(fila, "repeticiones_o_duracion", contexto),
            nivel=_campo(fila, "nivel", contexto),
            descanso=_campo(fila, "descanso", contexto),
        )

    @property
    def num_ejercicios(self) -> int:
        return len(self.ejercicios)

    def to_row(self) -> dict[str, str]:
        return {
            "id_plantilla": self.id_plantilla,
            "grupo_muscular": self.grupo_muscular,
            "ejercicios": "; ".join(self.ejercicios),
            "series": str(self.series),
            "repeticiones_o_duracion": self.repeticiones,
            "nivel": self.nivel,
            "descanso": self.descanso,
        }


@dataclass(frozen=True, slots=True)
class Ejercicio:
    id_ejercicio: str
    nombre: str
    grupo_muscular: str
    patron_movimiento: str
    equipamiento: str
    nivel_sugerido: str
    nota_tecnica: str

    @classmethod
    def from_row(cls, fila: Mapping[str, object]) -> "Ejercicio":
        id_ejercicio = _campo(fila, "id_ejercicio", "Ejercicio")
        contexto = f"Ejercicio {id_ejercicio}"
        return cls(
            id_ejercicio=id_ejercicio,
            nombre=_campo(fila, "nombre", contexto),
            grupo_muscular=_campo(fila, "grupo_muscular", contexto),
            patron_movimiento=_campo(fila, "patron_movimiento", contexto),
            equipamiento=_campo(fila, "equipamiento", contexto),
            nivel_sugerido=_campo(fila, "nivel_sugerido", contexto),
            nota_tecnica=_campo(fila, "nota_tecnica", contexto),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id_ejercicio": self.id_ejercicio,
            "nombre": self.nombre,
            "grupo_muscular": self.grupo_muscular,
            "patron_movimiento": self.patron_movimiento,
            "equipamiento": self.equipamiento,
            "nivel_sugerido": self.nivel_sugerido,
            "nota_tecnica": self.nota_tecnica,
        }


@dataclass(frozen=True, slots=True)
class Comida:
    id_plan: str
    comida: str
    horario: str
    alimentos: tuple[str, ...]
    objetivo_general: str
    observaciones: str

    @classmethod
    def from_row(cls, fila: Mapping[str, object]) -> "Comida":
        id_plan = _campo(fila, "id_plan", "Comida")
        contexto = f"Comida {id_plan}"
        alimentos = dividir_lista(_campo(fila, "alimentos_sugeridos", contexto))
        if not alimentos:
            raise DataValidationError(
                f"{contexto}: debe incluir al menos un alimento sugerido."
            )
        return cls(
            id_plan=id_plan,
            comida=_campo(fila, "comida", contexto),
            horario=_campo(fila, "horario", contexto),
            alimentos=alimentos,
            objetivo_general=_campo(fila, "objetivo_general", contexto),
            observaciones=_campo(fila, "observaciones", contexto),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id_plan": self.id_plan,
            "comida": self.comida,
            "horario": self.horario,
            "alimentos_sugeridos": "; ".join(self.alimentos),
            "objetivo_general": self.objetivo_general,
            "observaciones": self.observaciones,
        }


@dataclass(frozen=True, slots=True)
class Cobertura:
    usados: tuple[str, ...] = ()
    encontrados: tuple[str, ...] = ()
    faltantes: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return len(self.usados)

    @property
    def porcentaje(self) -> float:
        if not self.usados:
            return 100.0
        return len(self.encontrados) / len(self.usados) * 100.0
