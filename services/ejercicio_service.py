from collections.abc import Iterable
from pathlib import Path

from app.config import CATALOGO_PATH, COLUMNAS_EJERCICIO
from app.exceptions import DataValidationError
from app.models import Cobertura, Ejercicio, Rutina
from app.utils import normalizar_texto
from services.csv_service import CsvService


class EjercicioService:
    def __init__(
        self,
        csv_service: CsvService,
        ruta: str | Path = CATALOGO_PATH,
    ) -> None:
        self.csv_service = csv_service
        self.ruta = Path(ruta)
        self._ejercicios: tuple[Ejercicio, ...] = ()

    def cargar(self, ruta: str | Path | None = None) -> int:
        archivo = Path(ruta) if ruta is not None else self.ruta
        filas = self.csv_service.leer(
            archivo,
            COLUMNAS_EJERCICIO,
            columna_id="id_ejercicio",
        )

        ejercicios: list[Ejercicio] = []
        for fila in filas:
            try:
                ejercicios.append(Ejercicio.from_row(fila))
            except DataValidationError as exc:
                raise DataValidationError(
                    f"Error en '{archivo.name}': {exc}"
                ) from exc

        self.ruta = archivo
        self._ejercicios = tuple(ejercicios)
        return len(self._ejercicios)

    def todos(self) -> tuple[Ejercicio, ...]:
        return self._ejercicios

    def total(self) -> int:
        return len(self._ejercicios)

    def por_id(self, id_ejercicio: str) -> Ejercicio | None:
        for ejercicio in self._ejercicios:
            if ejercicio.id_ejercicio == id_ejercicio:
                return ejercicio
        return None

    def por_nombre(self, nombre: str) -> Ejercicio | None:
        buscado = normalizar_texto(nombre)
        for ejercicio in self._ejercicios:
            if normalizar_texto(ejercicio.nombre) == buscado:
                return ejercicio
        return None

    def filtrar(
        self,
        grupo: str = "",
        nivel: str = "",
        patron: str = "",
        equipo: str = "",
        texto: str = "",
    ) -> tuple[Ejercicio, ...]:
        return tuple(
            ejercicio
            for ejercicio in self._ejercicios
            if self._coincide(ejercicio.grupo_muscular, grupo)
            and self._coincide(ejercicio.nivel_sugerido, nivel)
            and self._coincide(ejercicio.patron_movimiento, patron)
            and self._coincide(ejercicio.equipamiento, equipo)
            and self._coincide_texto(ejercicio, texto)
        )

    @staticmethod
    def _coincide(valor: str, filtro: str) -> bool:
        filtro_limpio = (filtro or "").strip()
        if not filtro_limpio:
            return True
        return normalizar_texto(valor) == normalizar_texto(filtro_limpio)

    @staticmethod
    def _coincide_texto(ejercicio: Ejercicio, texto: str) -> bool:
        terminos = normalizar_texto(texto).split()
        if not terminos:
            return True

        contenido = normalizar_texto(
            " | ".join(
                (
                    ejercicio.id_ejercicio,
                    ejercicio.nombre,
                    ejercicio.grupo_muscular,
                    ejercicio.patron_movimiento,
                    ejercicio.equipamiento,
                    ejercicio.nivel_sugerido,
                    ejercicio.nota_tecnica,
                )
            )
        )
        return all(termino in contenido for termino in terminos)

    def grupos(self) -> list[str]:
        return sorted(
            {ejercicio.grupo_muscular for ejercicio in self._ejercicios},
            key=normalizar_texto,
        )

    def niveles(self) -> list[str]:
        return sorted(
            {ejercicio.nivel_sugerido for ejercicio in self._ejercicios},
            key=normalizar_texto,
        )

    def patrones(self) -> list[str]:
        return sorted(
            {ejercicio.patron_movimiento for ejercicio in self._ejercicios},
            key=normalizar_texto,
        )

    def equipamientos(self) -> list[str]:
        return sorted(
            {ejercicio.equipamiento for ejercicio in self._ejercicios},
            key=normalizar_texto,
        )

    def cobertura(self, rutinas: Iterable[Rutina]) -> Cobertura:
        nombres_usados: dict[str, str] = {}
        for rutina in rutinas:
            for nombre in rutina.ejercicios:
                clave = normalizar_texto(nombre)
                if clave and clave not in nombres_usados:
                    nombres_usados[clave] = nombre.strip()

        nombres_catalogo = {
            normalizar_texto(ejercicio.nombre)
            for ejercicio in self._ejercicios
        }

        encontrados = [
            nombre
            for clave, nombre in nombres_usados.items()
            if clave in nombres_catalogo
        ]
        faltantes = [
            nombre
            for clave, nombre in nombres_usados.items()
            if clave not in nombres_catalogo
        ]

        return Cobertura(
            usados=tuple(sorted(nombres_usados.values(), key=normalizar_texto)),
            encontrados=tuple(sorted(encontrados, key=normalizar_texto)),
            faltantes=tuple(sorted(faltantes, key=normalizar_texto)),
        )
