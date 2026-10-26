from pathlib import Path

from app.config import COLUMNAS_NUTRICION, NUTRICION_PATH
from app.exceptions import DataValidationError
from app.models import Comida
from app.utils import clave_horario, normalizar_texto
from services.csv_service import CsvService


class NutricionService:
    def __init__(
        self,
        csv_service: CsvService,
        ruta: str | Path = NUTRICION_PATH,
    ) -> None:
        self.csv_service = csv_service
        self.ruta = Path(ruta)
        self._comidas: tuple[Comida, ...] = ()

    def cargar(self, ruta: str | Path | None = None) -> int:
        archivo = Path(ruta) if ruta is not None else self.ruta
        filas = self.csv_service.leer(
            archivo,
            COLUMNAS_NUTRICION,
            columna_id="id_plan",
        )

        comidas: list[Comida] = []
        for fila in filas:
            try:
                comidas.append(Comida.from_row(fila))
            except DataValidationError as exc:
                raise DataValidationError(
                    f"Error en '{archivo.name}': {exc}"
                ) from exc

        self.ruta = archivo
        self._comidas = tuple(comidas)
        return len(self._comidas)

    def todos(self) -> tuple[Comida, ...]:
        return self._comidas

    def total(self) -> int:
        return len(self._comidas)

    def por_id(self, id_plan: str) -> Comida | None:
        for comida in self._comidas:
            if comida.id_plan == id_plan:
                return comida
        return None

    def filtrar(
        self,
        comida: str = "",
        horario: str = "",
        objetivo: str = "",
        texto: str = "",
    ) -> tuple[Comida, ...]:
        return tuple(
            registro
            for registro in self._comidas
            if self._coincide(registro.comida, comida)
            and self._coincide(registro.horario, horario)
            and self._coincide(registro.objetivo_general, objetivo)
            and self._coincide_texto(registro, texto)
        )

    @staticmethod
    def _coincide(valor: str, filtro: str) -> bool:
        filtro_limpio = (filtro or "").strip()
        if not filtro_limpio:
            return True
        return normalizar_texto(valor) == normalizar_texto(filtro_limpio)

    @staticmethod
    def _coincide_texto(comida: Comida, texto: str) -> bool:
        terminos = normalizar_texto(texto).split()
        if not terminos:
            return True

        contenido = normalizar_texto(
            " | ".join(
                (
                    comida.id_plan,
                    comida.comida,
                    comida.horario,
                    "; ".join(comida.alimentos),
                    comida.objetivo_general,
                    comida.observaciones,
                )
            )
        )
        return all(termino in contenido for termino in terminos)

    def comidas(self) -> list[str]:
        return sorted(
            {comida.comida for comida in self._comidas},
            key=normalizar_texto,
        )

    def horarios(self) -> list[str]:
        return sorted(
            {comida.horario for comida in self._comidas},
            key=lambda valor: (clave_horario(valor), normalizar_texto(valor)),
        )

    def objetivos(self) -> list[str]:
        return sorted(
            {comida.objetivo_general for comida in self._comidas},
            key=normalizar_texto,
        )

    def alimentos_unicos(self) -> list[str]:
        alimentos: dict[str, str] = {}
        for comida in self._comidas:
            for alimento in comida.alimentos:
                clave = normalizar_texto(alimento)
                if clave and clave not in alimentos:
                    alimentos[clave] = alimento.strip()
        return sorted(alimentos.values(), key=normalizar_texto)

    def total_sugerencias(self) -> int:
        return sum(len(comida.alimentos) for comida in self._comidas)
