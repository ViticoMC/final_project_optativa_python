from pathlib import Path

from app.config import COLUMNAS_RUTINA, DIAS, NIVELES, RUTINAS_PATH
from app.exceptions import DataValidationError
from app.models import Rutina
from app.utils import clave_horario, normalizar_texto
from services.csv_service import CsvService


class RutinaService:
    def __init__(
        self,
        csv_service: CsvService,
        ruta: str | Path = RUTINAS_PATH,
    ) -> None:
        self.csv_service = csv_service
        self.ruta = Path(ruta)
        self._rutinas: tuple[Rutina, ...] = ()

    def cargar(self, ruta: str | Path | None = None) -> int:
        archivo = Path(ruta) if ruta is not None else self.ruta
        filas = self.csv_service.leer(
            archivo,
            COLUMNAS_RUTINA,
            columna_id="id_rutina",
        )

        rutinas: list[Rutina] = []
        for fila in filas:
            try:
                rutinas.append(Rutina.from_row(fila))
            except DataValidationError as exc:
                raise DataValidationError(
                    f"Error en '{archivo.name}': {exc}"
                ) from exc

        self.ruta = archivo
        self._rutinas = tuple(rutinas)
        return len(self._rutinas)

    def todas(self) -> tuple[Rutina, ...]:
        return self._rutinas

    def total(self) -> int:
        return len(self._rutinas)

    def por_id(self, id_rutina: str) -> Rutina | None:
        for rutina in self._rutinas:
            if rutina.id_rutina == id_rutina:
                return rutina
        return None

    def filtrar(
        self,
        dia: str = "",
        grupo: str = "",
        nivel: str = "",
        horario: str = "",
        texto: str = "",
    ) -> tuple[Rutina, ...]:
        return tuple(
            rutina
            for rutina in self._rutinas
            if self._coincide(rutina.dia, dia)
            and self._coincide(rutina.grupo_muscular, grupo)
            and self._coincide(rutina.nivel, nivel)
            and self._coincide(rutina.horario, horario)
            and self._coincide_texto(rutina, texto)
        )

    @staticmethod
    def _coincide(valor: str, filtro: str) -> bool:
        filtro_limpio = (filtro or "").strip()
        if not filtro_limpio:
            return True
        return normalizar_texto(valor) == normalizar_texto(filtro_limpio)

    @staticmethod
    def _coincide_texto(rutina: Rutina, texto: str) -> bool:
        terminos = normalizar_texto(texto).split()
        if not terminos:
            return True

        contenido = normalizar_texto(
            " | ".join(
                (
                    rutina.id_rutina,
                    rutina.dia,
                    rutina.horario,
                    rutina.grupo_muscular,
                    "; ".join(rutina.ejercicios),
                    str(rutina.series),
                    rutina.repeticiones,
                    rutina.nivel,
                    rutina.descanso,
                )
            )
        )
        return all(termino in contenido for termino in terminos)

    def valores_unicos(self, campo: str) -> list[str]:
        if campo not in COLUMNAS_RUTINA:
            raise ValueError(f"Campo de rutina desconocido: {campo!r}.")

        valores = {rutina.to_row()[campo] for rutina in self._rutinas}
        return sorted(valores, key=normalizar_texto)

    def dias(self) -> list[str]:
        presentes = {rutina.dia for rutina in self._rutinas}
        conocidos = [dia for dia in DIAS if dia in presentes]
        otros = sorted(presentes - set(DIAS), key=normalizar_texto)
        return conocidos + otros

    def grupos(self) -> list[str]:
        return sorted(
            {rutina.grupo_muscular for rutina in self._rutinas},
            key=normalizar_texto,
        )

    def horarios(self) -> list[str]:
        return sorted(
            {rutina.horario for rutina in self._rutinas},
            key=lambda valor: (clave_horario(valor), valor),
        )

    def niveles(self) -> list[str]:
        presentes = {rutina.nivel for rutina in self._rutinas}
        conocidos = [nivel for nivel in NIVELES if nivel in presentes]
        otros = sorted(presentes - set(NIVELES), key=normalizar_texto)
        return conocidos + otros
